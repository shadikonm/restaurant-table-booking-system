from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import re
import os
import secrets
import hmac
import logging
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps
from contextlib import closing
from werkzeug.security import generate_password_hash, check_password_hash
from logging.handlers import RotatingFileHandler
from time import perf_counter
from flask import g, has_request_context
from assistant_service import answer_question
from db_integrity import install_invariants


app = Flask(__name__)

# Установите SECRET_KEY в окружении для стабильных сессий между перезапусками.
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    MAX_CONTENT_LENGTH=1024 * 1024,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
)
if not os.environ.get("SECRET_KEY"):
    app.logger.warning(
        "SECRET_KEY не задан: сессии сбросятся при перезапуске. Для публикации задайте SECRET_KEY."
    )

DATABASE = str(Path(__file__).resolve().parent / "restaurant.db")

# Мониторинг: журнал без паролей, телефонов, email и тела запросов.
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
if not any(isinstance(h, RotatingFileHandler) for h in app.logger.handlers):
    handler = RotatingFileHandler(
        LOG_DIR / "application.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)


@app.before_request
def start_request_timer():
    g.request_started = perf_counter()


@app.after_request
def log_request_metrics(response):
    duration_ms = round(
        (perf_counter() - getattr(g, "request_started", perf_counter())) * 1000, 1
    )
    # Не записываем query string и параметры форм (могут содержать личные данные).
    if response.status_code >= 400 or duration_ms > 1000:
        app.logger.warning(
            "HTTP method=%s path=%s status=%s duration_ms=%s",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
    response.headers["X-Response-Time-Ms"] = str(duration_ms)
    return response


@app.errorhandler(sqlite3.IntegrityError)
def integrity_error(error):
    message = str(error)
    if "reservation_conflict" in message:
        return jsonify(
            success=False, message="Стол уже занят на выбранный период."
        ), 409
    if "payment_required" in message:
        return jsonify(
            success=False, message="Сначала необходимо оплатить бронирование."
        ), 409
    app.logger.exception("Database integrity error")
    return jsonify(success=False, message="Не удалось сохранить данные."), 400


@app.errorhandler(500)
def internal_server_error(error):
    app.logger.error("Internal error path=%s", request.path, exc_info=True)
    if request.path.startswith("/api/"):
        return jsonify(success=False, message="Внутренняя ошибка сервера."), 500
    return "Внутренняя ошибка сервера. Попробуйте позже.", 500


@app.get("/health")
def health_check():
    # Доступен без входа; не раскрывает содержимое БД и настройки сервера.
    try:
        with closing(sqlite3.connect(DATABASE, timeout=2)) as conn:
            conn.execute("SELECT 1").fetchone()
        return jsonify(status="ok", database="ok"), 200
    except sqlite3.Error:
        app.logger.error("Health check failed: database unavailable")
        return jsonify(status="degraded", database="unavailable"), 503


@app.post("/api/assistant")
def assistant_reply():
    payload = request.get_json(silent=True) or {}
    question = payload.get("message", "")
    if not isinstance(question, str) or not question.strip() or len(question) > 500:
        return jsonify(
            success=False, message="Введите вопрос длиной до 500 символов."
        ), 400
    try:
        with closing(db()) as connection:
            items = connection.execute(
                "SELECT name, category, price FROM menu_items WHERE is_active = 1 ORDER BY id LIMIT 80"
            ).fetchall()
        result = answer_question(question, [dict(row) for row in items])
        return jsonify(success=True, answer=result["answer"], mode=result["mode"])
    except Exception:
        app.logger.exception("Assistant request failed")
        return jsonify(success=False, message="Помощник временно недоступен."), 503


@app.post("/api/assistant/book")
def assistant_book():
    """Assistant uses the same validation and booking logic as the public form."""
    data = request.get_json(silent=True) or {}
    try:
        guests = int(data.get("guests", 0))
    except (ValueError, TypeError):
        return jsonify(success=False, message="Укажите количество гостей."), 400
    if guests < 1 or guests > 6:
        return jsonify(
            success=False, message="Можно забронировать стол на 1–6 гостей."
        ), 400
    date, time = (
        str(data.get("reservation_date", "")),
        str(data.get("reservation_time", "")),
    )
    try:
        if datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M") <= datetime.now():
            raise ValueError()
    except ValueError:
        return jsonify(success=False, message="Укажите будущую дату и время."), 400
    # Prefer the smallest fitting table to avoid unnecessary deposit.
    for table, capacity in sorted(TABLES.items(), key=lambda x: (x[1], x[0])):
        if (
            capacity >= guests
            and table_is_active(table)
            and not busy(table, date, time)
        ):
            data["table_number"] = table
            data["preorder"] = []
            return create_reservation(data)
    return jsonify(
        success=False,
        message="На это время свободных столов нет. Выберите другое время.",
    ), 409


ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or secrets.token_urlsafe(32)
if not os.environ.get("ADMIN_PASSWORD"):
    app.logger.warning(
        "ADMIN_PASSWORD не задан: задайте его в окружении для входа администратора."
    )


# =========================================================
# НАСТРОЙКИ СТОЛОВ И БРОНИРОВАНИЯ
# =========================================================

TABLES = {
    # =========================
    # ОСНОВНОЙ ЗАЛ — 10 столов
    # =========================
    1: 2,
    2: 4,
    3: 4,
    4: 6,
    5: 4,
    6: 4,
    7: 6,
    8: 2,
    9: 4,
    10: 4,
    # =========================
    # ТЕРРАСА — 6 столов
    # =========================
    11: 2,
    12: 4,
    13: 4,
    14: 4,
    15: 2,
    16: 6,
}

BOOKING_DURATION_HOURS = 2


# Все допустимые статусы бронирования
ALLOWED_STATUSES = {"confirmed", "arrived", "completed", "cancelled"}


# Только эти статусы блокируют стол
ACTIVE_STATUSES = {"confirmed", "arrived"}


ALLOWED_PREORDER_STATUSES = {"new", "preparing", "ready"}


# =========================================================
# CSRF, ЗАЩИТА СЕССИЙ И УВЕДОМЛЕНИЯ
# =========================================================

# Автоматический бэкап один раз в сутки при первом запросе к работающему сайту.
# Не заменяет внешний планировщик: при выключенном сервере запусков не будет.
_last_backup_date = None


def automatic_daily_backup():
    global _last_backup_date
    today = datetime.now().strftime("%Y%m%d")
    if _last_backup_date == today:
        return
    source = Path(DATABASE)
    if not source.exists():
        return
    folder = source.parent / "backups"
    target = folder / f"restaurant_auto_{today}.db"
    try:
        folder.mkdir(exist_ok=True)
        if not target.exists():
            with (
                closing(sqlite3.connect(DATABASE)) as current,
                closing(sqlite3.connect(target)) as backup_db,
            ):
                current.backup(backup_db)
        _last_backup_date = today
    except Exception:
        app.logger.exception("Автоматический бэкап не создан")


@app.before_request
def protect_mutations():
    automatic_daily_backup()
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    session.permanent = True
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        token = request.headers.get("X-CSRF-Token") or request.form.get(
            "csrf_token", ""
        )
        if not hmac.compare_digest(str(token), session["_csrf_token"]):
            if request.path.startswith("/api/"):
                return jsonify(
                    success=False,
                    message="Сессия устарела. Обновите страницу и повторите действие.",
                ), 403
            return "Неверный CSRF-токен. Обновите страницу.", 403


@app.context_processor
def security_context():
    return {"csrf_token": lambda: session.get("_csrf_token", "")}


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; font-src 'self' data: https://fonts.googleapis.com https://fonts.gstatic.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "script-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    return response


def send_booking_email(recipient, subject, body):
    """Отправка только при настройке SMTP; сбой почты не ломает бронирование."""
    host = os.environ.get("SMTP_HOST")
    sender = os.environ.get("SMTP_FROM")
    if not host or not sender or not recipient:
        return False
    try:
        message = EmailMessage()
        message["From"] = sender
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        port = int(os.environ.get("SMTP_PORT", "587"))
        if os.environ.get("SMTP_SSL", "0") == "1":
            server = smtplib.SMTP_SSL(
                host, port, timeout=8, context=ssl.create_default_context()
            )
        else:
            server = smtplib.SMTP(host, port, timeout=8)
        with server:
            if os.environ.get("SMTP_SSL", "0") != "1":
                server.starttls(context=ssl.create_default_context())
            if os.environ.get("SMTP_USER"):
                server.login(
                    os.environ["SMTP_USER"], os.environ.get("SMTP_PASSWORD", "")
                )
            server.send_message(message)
        return True
    except Exception:
        app.logger.exception("Не удалось отправить email")
        return False


def email_for_user(connection, user_id):
    if not user_id:
        return None
    row = connection.execute(
        "SELECT email FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    return row["email"] if row else None


# =========================================================
# БАЗА ДАННЫХ
# =========================================================


def reset_auth_session():
    """Rotate the CSRF token when authentication state changes."""
    session.clear()
    session["_csrf_token"] = secrets.token_urlsafe(32)


def db():
    connection = sqlite3.connect(DATABASE, timeout=15)
    connection.row_factory = sqlite3.Row
    if has_request_context():
        g.setdefault("database_connections", []).append(connection)
    return connection


@app.teardown_request
def close_request_connections(error=None):
    for connection in g.pop("database_connections", []):
        connection.close()


def init_db():

    connection = db()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_number INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            guests INTEGER NOT NULL,
            reservation_date TEXT NOT NULL,
            reservation_time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'confirmed',
            user_id INTEGER,
            payment_status TEXT NOT NULL DEFAULT 'unpaid',
            payment_method TEXT,
            paid_at TEXT
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS table_settings (
            table_number INTEGER PRIMARY KEY,
            capacity INTEGER NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        )
        """
    )

    for table_number, capacity in TABLES.items():
        connection.execute(
            """
            INSERT INTO table_settings (table_number, capacity, is_active)
            VALUES (?, ?, 1)
            ON CONFLICT(table_number)
            DO UPDATE SET capacity = excluded.capacity
            """,
            (table_number, capacity),
        )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            price INTEGER NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reservation_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price INTEGER NOT NULL,
            FOREIGN KEY (reservation_id) REFERENCES reservations(id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
        )
        """
    )

    menu_count = connection.execute(
        "SELECT COUNT(*) AS count FROM menu_items"
    ).fetchone()["count"]

    if menu_count == 0:
        default_menu = [
            (
                "Тартар из говядины",
                "Говяжья вырезка, каперсы, корнишоны, дижонская горчица и хрустящий багет",
                "Закуски",
                4200,
            ),
            (
                "Брускетта с ростбифом",
                "Чиабатта, ростбиф, сливочный крем, руккола и вяленые томаты",
                "Закуски",
                3600,
            ),
            (
                "Креветки в чесночном масле",
                "Тигровые креветки, чеснок, сливочное масло и свежая зелень",
                "Закуски",
                4900,
            ),
            (
                "Салат с ростбифом",
                "Ростбиф, микс салатов, томаты черри, пармезан и горчичная заправка",
                "Салаты",
                3900,
            ),
            (
                "Цезарь с курицей",
                "Куриное филе, романо, пармезан, томаты черри и соус Цезарь",
                "Салаты",
                3400,
            ),
            (
                "Салат с лососем",
                "Слабосолёный лосось, авокадо, микс салатов и цитрусовая заправка",
                "Салаты",
                4400,
            ),
            (
                "Крем-суп из шампиньонов",
                "Шампиньоны, сливки, трюфельное масло и хрустящий багет",
                "Супы",
                2900,
            ),
            (
                "Тыквенный крем-суп",
                "Запечённая тыква, сливки, тыквенные семечки и ароматное масло",
                "Супы",
                2700,
            ),
            (
                "Томлёные говяжьи щёчки",
                "Говяжьи щёчки длительного томления, картофельное пюре и насыщенный мясной соус",
                "Горячие блюда",
                5900,
            ),
            (
                "Медальоны из телятины",
                "Телячья вырезка, картофель гратен и сливочно-грибной соус",
                "Горячие блюда",
                6900,
            ),
            (
                "Лосось со сливочным соусом",
                "Филе лосося, овощи гриль и сливочно-лимонный соус",
                "Горячие блюда",
                6500,
            ),
            (
                "Утиная грудка",
                "Утиная грудка, ягодный соус и картофельное пюре",
                "Горячие блюда",
                6200,
            ),
            (
                "Куриное филе с грибным соусом",
                "Куриное филе, картофельное пюре и сливочный соус с шампиньонами",
                "Горячие блюда",
                4500,
            ),
            (
                "Паста с креветками",
                "Феттучини, тигровые креветки, сливочный соус и пармезан",
                "Паста",
                4900,
            ),
            (
                "Феттучини с грибами",
                "Паста, шампиньоны, сливочный соус и пармезан",
                "Паста",
                3900,
            ),
            ("Карбонара", "Спагетти, бекон, желток и пармезан", "Паста", 4200),
            (
                "Тирамису",
                "Классический итальянский десерт с маскарпоне и кофе",
                "Десерты",
                2600,
            ),
            (
                "Баскский чизкейк",
                "Нежный запечённый чизкейк с карамелизированной корочкой",
                "Десерты",
                2800,
            ),
            (
                "Шоколадный фондан",
                "Тёплый шоколадный десерт с жидким центром и мороженым",
                "Десерты",
                2900,
            ),
            (
                "Домашний лимонад",
                "Лимон, лайм, мята и газированная вода",
                "Напитки",
                1800,
            ),
            ("Апельсиновый фреш", "Свежевыжатый апельсиновый сок", "Напитки", 2200),
            ("Американо", "Классический чёрный кофе", "Напитки", 1200),
            ("Капучино", "Эспрессо и взбитое молоко", "Напитки", 1600),
        ]
        connection.executemany(
            "INSERT INTO menu_items (name, description, category, price, is_active) VALUES (?, ?, ?, ?, 1)",
            default_menu,
        )

    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(reservations)").fetchall()
    }

    if "user_id" not in columns:
        connection.execute("ALTER TABLE reservations ADD COLUMN user_id INTEGER")

    if "payment_status" not in columns:
        connection.execute(
            "ALTER TABLE reservations ADD COLUMN payment_status TEXT NOT NULL DEFAULT 'unpaid'"
        )

    if "payment_method" not in columns:
        connection.execute("ALTER TABLE reservations ADD COLUMN payment_method TEXT")

    if "paid_at" not in columns:
        connection.execute("ALTER TABLE reservations ADD COLUMN paid_at TEXT")

    if "special_requests" not in columns:
        connection.execute("ALTER TABLE reservations ADD COLUMN special_requests TEXT")

    if "comment" not in columns:
        connection.execute("ALTER TABLE reservations ADD COLUMN comment TEXT")

    if "payment_deadline" not in columns:
        connection.execute("ALTER TABLE reservations ADD COLUMN payment_deadline TEXT")

    if "preorder_status" not in columns:
        connection.execute("ALTER TABLE reservations ADD COLUMN preorder_status TEXT")

    connection.execute(
        """
        UPDATE reservations
        SET preorder_status = 'new'
        WHERE preorder_status IS NULL
          AND id IN (SELECT DISTINCT reservation_id FROM reservation_items)
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_username TEXT NOT NULL,
            action_type TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            description TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.execute("""CREATE TABLE IF NOT EXISTS email_reminders (
        reservation_id INTEGER PRIMARY KEY,
        sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    install_invariants(connection)
    connection.commit()
    connection.close()


# =========================================================
# АККАУНТ ПОСЕТИТЕЛЯ
# =========================================================


def user_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not session.get("user_id"):
            return redirect(url_for("user_login"))
        connection = db()
        exists = connection.execute(
            "SELECT 1 FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()
        connection.close()
        if not exists:
            reset_auth_session()
            return redirect(url_for("user_login"))
        return function(*args, **kwargs)

    return wrapper


@app.route("/register", methods=["GET", "POST"])
def register():

    if session.get("user_id"):
        return redirect(url_for("account"))

    error = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        if not 2 <= len(name) <= 50:
            error = "Введите имя от 2 до 50 символов."
        elif not valid_phone(phone):
            error = "Введите корректный номер телефона."
        elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            error = "Введите корректный email."
        elif len(password) < 8:
            error = "Пароль должен содержать минимум 8 символов."
        elif password != password2:
            error = "Пароли не совпадают."
        else:
            connection = db()
            existing = connection.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()

            if existing:
                connection.close()
                error = "Пользователь с таким email уже зарегистрирован."
            else:
                cursor = connection.execute(
                    """
                    INSERT INTO users (name, phone, email, password_hash)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, phone, email, generate_password_hash(password)),
                )
                user_id = cursor.lastrowid
                connection.commit()
                connection.close()

                reset_auth_session()
                session["user_id"] = user_id
                session["user_name"] = name
                session["user_email"] = email

                return redirect(url_for("account"))

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def user_login():

    if session.get("user_id"):
        return redirect(url_for("account"))

    error = None

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        connection = db()
        user = connection.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        connection.close()

        if not user or not check_password_hash(user["password_hash"], password):
            error = "Неверный email или пароль."
        else:
            reset_auth_session()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            return redirect(url_for("account"))

    return render_template("user_login.html", error=error)


@app.route("/logout")
def user_logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    session.pop("user_email", None)
    return redirect(url_for("home"))


@app.route("/account")
@user_required
def account():

    expire_unpaid_bookings()
    connection = db()
    user = connection.execute(
        "SELECT id, name, phone, email FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()

    reservation_rows = connection.execute(
        """
        SELECT id, table_number, customer_name, phone, guests,
               reservation_date, reservation_time, status,
               payment_status, payment_method, paid_at,
               special_requests, comment, preorder_status, payment_deadline
        FROM reservations
        WHERE user_id = ?
        ORDER BY reservation_date DESC, reservation_time DESC, id DESC
        """,
        (session["user_id"],),
    ).fetchall()

    reservations = []
    for row in reservation_rows:
        reservation = dict(row)
        preorder_items, preorder_total = get_reservation_preorder(
            connection, reservation["id"]
        )
        reservation["preorder_items"] = preorder_items
        reservation["preorder_total"] = preorder_total
        reservation["deposit_required"] = requires_deposit(
            reservation["guests"], reservation["table_number"], bool(preorder_items)
        )
        reservations.append(reservation)

    connection.close()

    return render_template(
        "account.html", user=user, reservations=reservations, now=datetime.now()
    )


@app.route("/account/profile", methods=["POST"])
@user_required
def update_profile():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    if not 2 <= len(name) <= 50 or not valid_phone(phone):
        return redirect(url_for("account", profile_error="1"))
    connection = db()
    connection.execute(
        "UPDATE users SET name = ?, phone = ? WHERE id = ?",
        (name, phone, session["user_id"]),
    )
    connection.commit()
    connection.close()
    session["user_name"] = name
    return redirect(url_for("account", profile_saved="1"))


@app.route("/account/reservations/<int:rid>/cancel", methods=["POST"])
@user_required
def account_cancel_reservation(rid):

    connection = db()
    reservation = connection.execute(
        """
        SELECT id, reservation_date, reservation_time, status, user_id
        FROM reservations
        WHERE id = ? AND user_id = ?
        """,
        (rid, session["user_id"]),
    ).fetchone()

    if not reservation:
        connection.close()
        return redirect(url_for("account"))

    if reservation["status"] not in {"confirmed", "pending_payment"}:
        connection.close()
        return redirect(url_for("account"))

    try:
        reservation_datetime = datetime.strptime(
            f"{reservation['reservation_date']} {reservation['reservation_time']}",
            "%Y-%m-%d %H:%M",
        )
    except ValueError:
        connection.close()
        return redirect(url_for("account"))

    if reservation_datetime < datetime.now():
        connection.close()
        return redirect(url_for("account"))

    connection.execute(
        """
        UPDATE reservations
        SET status = 'cancelled',
            payment_status = CASE
                WHEN payment_status = 'paid' THEN 'refunded'
                ELSE payment_status
            END
        WHERE id = ?
        """,
        (rid,),
    )
    recipient = email_for_user(connection, session["user_id"])
    connection.commit()
    connection.close()
    send_booking_email(
        recipient,
        "Отмена бронирования TABLE",
        f"Бронирование №{rid} отменено. Если депозит был оплачен, в демонстрационной системе отмечен возврат.",
    )
    return redirect(url_for("account"))


# =========================================================
# DEMO-ОПЛАТА БРОНИРОВАНИЯ
# =========================================================


@app.route("/payment/<int:rid>", methods=["GET", "POST"])
def payment(rid):
    connection = db()
    reservation = connection.execute(
        """
        SELECT id, table_number, guests, reservation_date, reservation_time,
               status, payment_status, payment_method, paid_at,
               customer_name, user_id, payment_deadline
        FROM reservations
        WHERE id = ?
        """,
        (rid,),
    ).fetchone()

    if not can_view_payment(reservation):
        connection.close()
        return redirect(url_for("home"))

    expire_unpaid_bookings()
    reservation = connection.execute(
        "SELECT * FROM reservations WHERE id=?", (rid,)
    ).fetchone()
    preorder_items, preorder_total = get_reservation_preorder(connection, rid)
    deposit_required = requires_deposit(
        reservation["guests"], reservation["table_number"], bool(preorder_items)
    )
    if not deposit_required:
        connection.close()
        return redirect(url_for("home"))

    error = None
    amount = 5000

    if request.method == "POST":
        method = request.form.get("payment_method", "").strip()
        allowed_methods = {"card", "kaspi", "apple_pay"}

        if reservation["status"] == "cancelled":
            error = "Отменённое бронирование нельзя оплатить."
        elif reservation["status"] == "completed":
            error = "Завершённое бронирование нельзя оплатить."
        elif reservation["payment_status"] == "paid":
            connection.close()
            return redirect(url_for("payment_success", rid=rid))
        elif reservation["status"] != "pending_payment":
            error = "Эта бронь не ожидает предоплату."
        elif method not in allowed_methods:
            error = "Выберите способ оплаты."
        elif method == "card" and request.form.get("demo_card_confirmed") != "yes":
            error = "Для демонстрации используйте только тестовую карту 4242 4242 4242 4242."
        elif method == "kaspi" and request.form.get("demo_qr_confirmed") != "yes":
            error = "Подтвердите ознакомление с демонстрационным QR."
        elif (
            method == "apple_pay" and request.form.get("demo_wallet_confirmed") != "yes"
        ):
            error = "Подтвердите демонстрационную оплату."
        else:
            paid_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            connection.execute(
                """
                UPDATE reservations
                SET payment_status = 'paid', status = 'confirmed',
                    payment_deadline = NULL, payment_method = ?,
                    paid_at = ?
                WHERE id = ? AND status = 'pending_payment'
                """,
                (method, paid_at, rid),
            )
            connection.commit()
            recipient = email_for_user(connection, reservation["user_id"])
            connection.close()
            send_booking_email(
                recipient,
                "Бронирование TABLE подтверждено",
                f"Бронь №{rid}: стол №{reservation['table_number']}, "
                f"{reservation['reservation_date']} в {reservation['reservation_time']}.",
            )
            return redirect(url_for("payment_success", rid=rid))

    connection.close()
    return render_template(
        "payment.html",
        reservation=reservation,
        amount=amount,
        error=error,
        preorder_total=preorder_total,
        table_capacity=TABLES[reservation["table_number"]],
    )


@app.route("/payment/<int:rid>/success")
def payment_success(rid):
    connection = db()
    reservation = connection.execute(
        """
        SELECT id, table_number, guests, customer_name, reservation_date, reservation_time,
               payment_status, payment_method, paid_at, status, user_id
        FROM reservations
        WHERE id = ?
        """,
        (rid,),
    ).fetchone()
    preorder_items, preorder_total = (
        get_reservation_preorder(connection, rid) if reservation else ([], 0)
    )
    connection.close()

    if not can_view_payment(reservation) or reservation["payment_status"] != "paid":
        return redirect(url_for("home"))

    return render_template(
        "payment_success.html",
        reservation=reservation,
        amount=5000,
        preorder_items=preorder_items,
        preorder_total=preorder_total,
    )


# =========================================================
# ЗАЩИТА АДМИН-ПАНЕЛИ
# =========================================================


def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))

        return function(*args, **kwargs)

    return wrapper


def admin_api_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not session.get("admin_logged_in"):
            return jsonify(success=False, message="Необходим вход администратора."), 401

        return function(*args, **kwargs)

    return wrapper


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================================================


def valid_phone(phone):

    digits = re.sub(r"\D", "", phone)

    return 10 <= len(digits) <= 12


def normalize_phone(phone):

    return re.sub(r"\D", "", str(phone))


def normalize_name(name):
    return " ".join(str(name).strip().casefold().split())


def add_admin_log(
    connection,
    action_type,
    entity_type,
    entity_id,
    description,
    old_value=None,
    new_value=None,
):
    connection.execute(
        """
        INSERT INTO admin_logs (
            admin_username, action_type, entity_type, entity_id,
            description, old_value, new_value
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session.get("admin_username", "admin"),
            action_type,
            entity_type,
            entity_id,
            description,
            None if old_value is None else str(old_value),
            None if new_value is None else str(new_value),
        ),
    )


def overlap(time_a, time_b):

    first = datetime.strptime(time_a, "%H:%M")

    second = datetime.strptime(time_b, "%H:%M")

    first_end = first + timedelta(hours=BOOKING_DURATION_HOURS)

    second_end = second + timedelta(hours=BOOKING_DURATION_HOURS)

    return second < first_end and first < second_end


def table_is_active(table_number):
    connection = db()
    row = connection.execute(
        "SELECT is_active FROM table_settings WHERE table_number = ?", (table_number,)
    ).fetchone()
    connection.close()
    return bool(row["is_active"]) if row is not None else table_number in TABLES


def expire_unpaid_bookings():
    """Release unpaid provisional bookings after 15 minutes."""
    with closing(db()) as conn:
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not conn.execute(
            "SELECT 1 FROM reservations WHERE status='pending_payment' AND payment_deadline < ? LIMIT 1",
            (now_text,),
        ).fetchone():
            return
        conn.execute(
            """UPDATE reservations SET status='cancelled'
                        WHERE status='pending_payment' AND payment_deadline IS NOT NULL
                        AND payment_deadline < ?""",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),),
        )
        conn.commit()


def requires_deposit(guests, table_number, has_preorder=False):
    capacity = TABLES.get(table_number, 0)
    return (
        guests > 4
        or bool(has_preorder)
        or (guests == 4 and capacity == 6)
        or (guests in (1, 2) and capacity > 2)
    )


def can_view_payment(reservation):
    return reservation is not None and (
        reservation["user_id"] == session.get("user_id")
        and session.get("user_id") is not None
        or reservation["id"] in session.get("guest_payment_ids", [])
    )


def busy(table_number, reservation_date, reservation_time, exclude=None):

    expire_unpaid_bookings()
    connection = db()

    sql = """
        SELECT
            id,
            reservation_time
        FROM reservations
        WHERE table_number = ?
        AND reservation_date = ?
        AND status IN ('confirmed', 'arrived', 'pending_payment')
    """

    params = [table_number, reservation_date]

    if exclude is not None:
        sql += " AND id != ?"
        params.append(exclude)

    rows = connection.execute(sql, params).fetchall()

    connection.close()

    return any(overlap(row["reservation_time"], reservation_time) for row in rows)


# =========================================================
# ГЛАВНАЯ СТРАНИЦА
# =========================================================


@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# ВХОД АДМИНИСТРАТОРА
# =========================================================


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()

        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and hmac.compare_digest(password, ADMIN_PASSWORD):
            reset_auth_session()

            session["admin_logged_in"] = True

            session["admin_username"] = ADMIN_USERNAME

            return redirect(url_for("admin"))

        error = "Неверный логин или пароль."

    return render_template("login.html", error=error)


@app.route("/admin/logout")
def admin_logout():

    reset_auth_session()

    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin():

    return render_template(
        "admin.html", admin_username=session.get("admin_username", "admin")
    )


# =========================================================
# ПРОВЕРКА ДОСТУПНОСТИ СТОЛОВ
# =========================================================


@app.route("/api/availability")
def availability():

    date = request.args.get("date", "")

    time = request.args.get("time", "")

    guests = request.args.get("guests", type=int)

    if not date or not time or not guests:
        return jsonify(
            success=False, message="Выберите дату, время и количество гостей."
        ), 400

    try:
        reservation_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

    except ValueError:
        return jsonify(success=False, message="Некорректная дата или время."), 400

    if reservation_datetime < datetime.now():
        return jsonify(success=False, message="Нельзя выбрать прошедшее время."), 400

    unsuitable_tables = [
        table_number for table_number, capacity in TABLES.items() if capacity < guests
    ]

    expire_unpaid_bookings()
    with closing(db()) as connection:
        disabled_tables = [
            row["table_number"]
            for row in connection.execute(
                "SELECT table_number FROM table_settings WHERE is_active = 0"
            )
        ]
        occupied = {
            row["table_number"]
            for row in connection.execute(
                """SELECT table_number FROM reservations
               WHERE status IN ('confirmed','arrived','pending_payment')
               AND julianday(reservation_date || ' ' || reservation_time)
                   < julianday(?, '+2 hours')
               AND julianday(?) < julianday(reservation_date || ' ' || reservation_time, '+2 hours')""",
                (f"{date} {time}", f"{date} {time}"),
            )
        }
    busy_tables = [
        number
        for number, capacity in TABLES.items()
        if capacity >= guests and (number in disabled_tables or number in occupied)
    ]

    return jsonify(
        success=True,
        busy_tables=busy_tables,
        unsuitable_tables=unsuitable_tables,
        disabled_tables=disabled_tables,
    )


# =========================================================
# СОЗДАНИЕ НОВОЙ БРОНИ
# =========================================================


@app.route("/api/reservations", methods=["POST"])
def create_reservation(data=None):

    if data is None:
        data = request.get_json(silent=True) or {}

    name = str(data.get("customer_name", "")).strip()

    phone = str(data.get("phone", "")).strip()

    raw_special_requests = data.get("special_requests", [])
    if not isinstance(raw_special_requests, list):
        raw_special_requests = []

    allowed_special_requests = {
        "window",
        "child_chair",
        "birthday",
        "quiet",
        "accessible",
    }
    special_requests = [
        str(item).strip()
        for item in raw_special_requests
        if str(item).strip() in allowed_special_requests
    ]
    special_requests_text = ",".join(dict.fromkeys(special_requests))

    comment = str(data.get("comment", "")).strip()
    if len(comment) > 500:
        return jsonify(success=False, message="Комментарий слишком длинный."), 400

    raw_preorder = data.get("preorder", [])
    if not isinstance(raw_preorder, list):
        return jsonify(success=False, message="Некорректный предзаказ блюд."), 400

    preorder_quantities = {}
    for item in raw_preorder:
        if not isinstance(item, dict):
            return jsonify(success=False, message="Некорректный предзаказ блюд."), 400
        try:
            menu_item_id = int(item.get("menu_item_id"))
            quantity = int(item.get("quantity"))
        except (TypeError, ValueError):
            return jsonify(success=False, message="Некорректный предзаказ блюд."), 400
        if quantity < 1 or quantity > 20:
            return jsonify(
                success=False, message="Количество одного блюда должно быть от 1 до 20."
            ), 400
        preorder_quantities[menu_item_id] = (
            preorder_quantities.get(menu_item_id, 0) + quantity
        )

    date = str(data.get("reservation_date", "")).strip()

    time = str(data.get("reservation_time", "")).strip()

    try:
        table = int(data.get("table_number"))

        guests = int(data.get("guests"))

    except (TypeError, ValueError):
        return jsonify(success=False, message="Некорректные данные."), 400

    if not 2 <= len(name) <= 50:
        return jsonify(success=False, message="Введите корректное имя."), 400

    if not valid_phone(phone):
        return jsonify(success=False, message="Введите корректный телефон."), 400

    if table not in TABLES or guests < 1 or guests > TABLES[table]:
        return jsonify(
            success=False, message="Стол не подходит для этого количества гостей."
        ), 400

    if not table_is_active(table):
        return jsonify(
            success=False, message="Этот стол временно недоступен для бронирования."
        ), 409

    try:
        reservation_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

    except ValueError:
        return jsonify(success=False, message="Некорректная дата или время."), 400

    if reservation_datetime < datetime.now():
        return jsonify(
            success=False, message="Нельзя бронировать прошедшее время."
        ), 400

    if busy(table, date, time):
        return jsonify(
            success=False, message="Этот стол уже занят на выбранный период."
        ), 409

    connection = db()

    reservation_user_id = None
    logged_in_user_id = session.get("user_id")

    if logged_in_user_id:
        logged_in_user = connection.execute(
            "SELECT id, name, phone FROM users WHERE id = ?", (logged_in_user_id,)
        ).fetchone()

        if (
            logged_in_user
            and normalize_name(logged_in_user["name"]) == normalize_name(name)
            and normalize_phone(logged_in_user["phone"]) == normalize_phone(phone)
        ):
            reservation_user_id = logged_in_user["id"]

    payment_needed = requires_deposit(guests, table, bool(preorder_quantities))
    initial_status = "pending_payment" if payment_needed else "confirmed"
    deadline = (
        (datetime.now() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
        if payment_needed
        else None
    )
    cursor = connection.execute(
        """
        INSERT INTO reservations (
            table_number,
            customer_name,
            phone,
            guests,
            reservation_date,
            reservation_time,
            status,
            user_id,
            special_requests,
            comment, payment_deadline
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            table,
            name,
            phone,
            guests,
            date,
            time,
            initial_status,
            reservation_user_id,
            special_requests_text,
            comment,
            deadline,
        ),
    )

    reservation_id = cursor.lastrowid
    preorder_total = 0

    if preorder_quantities:
        menu_ids = list(preorder_quantities.keys())
        placeholders = ",".join("?" for _ in menu_ids)
        menu_rows = connection.execute(
            f"SELECT id, price FROM menu_items WHERE is_active = 1 AND id IN ({placeholders})",
            menu_ids,
        ).fetchall()
        menu_by_id = {row["id"]: row for row in menu_rows}

        if len(menu_by_id) != len(menu_ids):
            connection.rollback()
            connection.close()
            return jsonify(
                success=False, message="Одно из выбранных блюд больше недоступно."
            ), 400

        for menu_item_id, quantity in preorder_quantities.items():
            unit_price = menu_by_id[menu_item_id]["price"]
            preorder_total += unit_price * quantity
            connection.execute(
                """
                INSERT INTO reservation_items (reservation_id, menu_item_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
                """,
                (reservation_id, menu_item_id, quantity, unit_price),
            )

        connection.execute(
            "UPDATE reservations SET preorder_status = 'new' WHERE id = ?",
            (reservation_id,),
        )

    recipient = email_for_user(connection, reservation_user_id)
    connection.commit()
    connection.close()
    if payment_needed:
        session["guest_payment_ids"] = (
            session.get("guest_payment_ids", []) + [reservation_id]
        )[-20:]
    else:
        send_booking_email(
            recipient,
            "Бронирование TABLE подтверждено",
            f"Ваша бронь №{reservation_id}: стол №{table}, {date} в {time}, гостей: {guests}.",
        )

    return jsonify(
        success=True,
        reservation_id=reservation_id,
        preorder_total=preorder_total,
        payment_required=payment_needed,
        payment_url=url_for("payment", rid=reservation_id) if payment_needed else None,
    )


# =========================================================
# МЕНЮ И ПРЕДЗАКАЗ БЛЮД
# =========================================================


@app.route("/api/menu", methods=["GET"])
def get_menu():
    connection = db()
    rows = connection.execute(
        """
        SELECT id, name, description, category, price
        FROM menu_items
        WHERE is_active = 1
        ORDER BY
            CASE category
                WHEN 'Закуски' THEN 1
                WHEN 'Салаты' THEN 2
                WHEN 'Супы' THEN 3
                WHEN 'Горячие блюда' THEN 4
                WHEN 'Паста' THEN 5
                WHEN 'Десерты' THEN 6
                WHEN 'Напитки' THEN 7
                ELSE 8
            END, id
        """
    ).fetchall()
    connection.close()
    return jsonify(success=True, menu=[dict(row) for row in rows])


def get_reservation_preorder(connection, reservation_id):
    rows = connection.execute(
        """
        SELECT ri.menu_item_id, mi.name, mi.category, ri.quantity, ri.unit_price,
               ri.quantity * ri.unit_price AS total
        FROM reservation_items AS ri
        JOIN menu_items AS mi ON mi.id = ri.menu_item_id
        WHERE ri.reservation_id = ?
        ORDER BY mi.category, mi.name
        """,
        (reservation_id,),
    ).fetchall()
    items = [dict(row) for row in rows]
    return items, sum(item["total"] for item in items)


# =========================================================
# УПРАВЛЕНИЕ СТОЛИКАМИ ДЛЯ АДМИНА
# =========================================================


@app.route("/api/admin/tables", methods=["GET"])
@admin_api_required
def admin_tables():
    connection = db()
    rows = connection.execute(
        "SELECT table_number, capacity, is_active FROM table_settings ORDER BY table_number"
    ).fetchall()
    connection.close()
    return jsonify(
        success=True,
        tables=[
            {
                "table_number": row["table_number"],
                "capacity": row["capacity"],
                "is_active": bool(row["is_active"]),
            }
            for row in rows
        ],
    )


@app.route("/api/admin/tables/<int:table_number>/status", methods=["PATCH"])
@admin_api_required
def update_table_status(table_number):
    if table_number not in TABLES:
        return jsonify(success=False, message="Стол не найден."), 404
    data = request.get_json(silent=True) or {}
    is_active = data.get("is_active")
    if not isinstance(is_active, bool):
        return jsonify(success=False, message="Некорректный статус столика."), 400
    connection = db()
    current = connection.execute(
        "SELECT is_active FROM table_settings WHERE table_number = ?", (table_number,)
    ).fetchone()
    old_active = bool(current["is_active"]) if current else True

    connection.execute(
        "INSERT INTO table_settings (table_number, capacity, is_active) VALUES (?, ?, ?) "
        "ON CONFLICT(table_number) DO UPDATE SET capacity = excluded.capacity, is_active = excluded.is_active",
        (table_number, TABLES[table_number], 1 if is_active else 0),
    )

    if old_active != is_active:
        add_admin_log(
            connection,
            "table_status_changed",
            "table",
            table_number,
            f"Стол №{table_number}: {'включён' if is_active else 'отключён'}",
            "active" if old_active else "inactive",
            "active" if is_active else "inactive",
        )

    connection.commit()
    connection.close()
    return jsonify(success=True, table_number=table_number, is_active=is_active)


# =========================================================
# ПОЛУЧЕНИЕ ВСЕХ БРОНЕЙ ДЛЯ АДМИНА
# =========================================================


@app.route("/api/reservations", methods=["GET"])
@admin_api_required
def list_reservations():

    connection = db()

    rows = connection.execute(
        """
        SELECT
            id,
            table_number,
            customer_name,
            phone,
            guests,
            reservation_date,
            reservation_time,
            status,
            payment_status,
            payment_method,
            paid_at,
            special_requests,
            comment,
            preorder_status
        FROM reservations
        ORDER BY
            reservation_date ASC,
            reservation_time ASC,
            id ASC
        """
    ).fetchall()

    reservations = []
    for row in rows:
        reservation = dict(row)
        preorder_items, preorder_total = get_reservation_preorder(
            connection, reservation["id"]
        )
        reservation["preorder_items"] = preorder_items
        reservation["preorder_total"] = preorder_total
        reservations.append(reservation)

    connection.close()

    return jsonify(success=True, reservations=reservations)


# =========================================================
# РЕДАКТИРОВАНИЕ БРОНИ АДМИНИСТРАТОРОМ
# =========================================================


@app.route("/api/reservations/<int:rid>", methods=["PUT"])
@admin_api_required
def update_reservation(rid):

    data = request.get_json(silent=True) or {}

    name = str(data.get("customer_name", "")).strip()

    phone = str(data.get("phone", "")).strip()

    date = str(data.get("reservation_date", "")).strip()

    time = str(data.get("reservation_time", "")).strip()

    try:
        table = int(data.get("table_number"))

        guests = int(data.get("guests"))

    except (TypeError, ValueError):
        return jsonify(success=False, message="Некорректные данные."), 400

    if not 2 <= len(name) <= 50 or not valid_phone(phone):
        return jsonify(success=False, message="Проверьте имя и телефон."), 400

    if table not in TABLES or guests < 1 or guests > TABLES[table]:
        return jsonify(
            success=False, message="Стол не подходит для этого количества гостей."
        ), 400

    if not table_is_active(table):
        return jsonify(
            success=False, message="Этот стол временно отключён администратором."
        ), 409

    try:
        datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

    except ValueError:
        return jsonify(success=False, message="Некорректная дата или время."), 400

    connection = db()

    reservation = connection.execute(
        """
        SELECT
            id, table_number, customer_name, phone, guests,
            reservation_date, reservation_time, status
        FROM reservations
        WHERE id = ?
        """,
        (rid,),
    ).fetchone()

    connection.close()

    if not reservation:
        return jsonify(success=False, message="Бронь не найдена."), 404

    if reservation["status"] in {"completed", "cancelled"}:
        return jsonify(
            success=False,
            message="Завершённую или отменённую бронь нельзя редактировать.",
        ), 400

    if busy(table, date, time, rid):
        return jsonify(success=False, message="Стол уже занят."), 409

    connection = db()

    connection.execute(
        """
        UPDATE reservations
        SET
            table_number = ?,
            customer_name = ?,
            phone = ?,
            guests = ?,
            reservation_date = ?,
            reservation_time = ?
        WHERE id = ?
        """,
        (table, name, phone, guests, date, time, rid),
    )

    old_summary = (
        f"Стол {reservation['table_number']}; {reservation['customer_name']}; "
        f"{reservation['phone']}; гостей {reservation['guests']}; "
        f"{reservation['reservation_date']} {reservation['reservation_time']}"
    )
    new_summary = f"Стол {table}; {name}; {phone}; гостей {guests}; {date} {time}"

    if old_summary != new_summary:
        add_admin_log(
            connection,
            "reservation_edited",
            "reservation",
            rid,
            f"Отредактировано бронирование #{rid}",
            old_summary,
            new_summary,
        )

    connection.commit()
    connection.close()

    return jsonify(success=True)


# =========================================================
# ИЗМЕНЕНИЕ СТАТУСА АДМИНИСТРАТОРОМ
# =========================================================


@app.route("/api/reservations/<int:rid>/status", methods=["PATCH"])
@admin_api_required
def update_reservation_status(rid):

    data = request.get_json(silent=True) or {}

    new_status = str(data.get("status", "")).strip()

    if new_status not in ALLOWED_STATUSES:
        return jsonify(success=False, message="Недопустимый статус."), 400

    connection = db()

    reservation = connection.execute(
        """
        SELECT *
        FROM reservations
        WHERE id = ?
        """,
        (rid,),
    ).fetchone()

    connection.close()

    if not reservation:
        return jsonify(success=False, message="Бронь не найдена."), 404

    if new_status in ACTIVE_STATUSES:
        if busy(
            reservation["table_number"],
            reservation["reservation_date"],
            reservation["reservation_time"],
            rid,
        ):
            return jsonify(
                success=False,
                message=(
                    "Нельзя активировать бронь: стол уже занят другим бронированием."
                ),
            ), 409

    connection = db()

    connection.execute(
        """
        UPDATE reservations
        SET status = ?
        WHERE id = ?
        """,
        (new_status, rid),
    )

    if reservation["status"] != new_status:
        add_admin_log(
            connection,
            "reservation_status_changed",
            "reservation",
            rid,
            f"Изменён статус бронирования #{rid}",
            reservation["status"],
            new_status,
        )

    connection.commit()
    connection.close()

    return jsonify(success=True)


# =========================================================
# ИЗМЕНЕНИЕ СТАТУСА ПРЕДЗАКАЗА АДМИНИСТРАТОРОМ
# =========================================================


@app.route("/api/admin/reservations/<int:rid>/preorder-status", methods=["PATCH"])
@admin_api_required
def update_preorder_status(rid):

    data = request.get_json(silent=True) or {}
    new_status = str(data.get("status", "")).strip()

    if new_status not in ALLOWED_PREORDER_STATUSES:
        return jsonify(success=False, message="Недопустимый статус предзаказа."), 400

    connection = db()
    reservation = connection.execute(
        "SELECT id, preorder_status FROM reservations WHERE id = ?", (rid,)
    ).fetchone()

    if not reservation:
        connection.close()
        return jsonify(success=False, message="Бронирование не найдено."), 404

    preorder_exists = connection.execute(
        "SELECT id FROM reservation_items WHERE reservation_id = ? LIMIT 1", (rid,)
    ).fetchone()

    if not preorder_exists:
        connection.close()
        return jsonify(success=False, message="У этой брони нет предзаказа."), 400

    connection.execute(
        "UPDATE reservations SET preorder_status = ? WHERE id = ?", (new_status, rid)
    )

    if reservation["preorder_status"] != new_status:
        add_admin_log(
            connection,
            "preorder_status_changed",
            "reservation",
            rid,
            f"Изменён статус предзаказа для бронирования #{rid}",
            reservation["preorder_status"],
            new_status,
        )

    connection.commit()
    connection.close()

    return jsonify(success=True, preorder_status=new_status)


# =========================================================
# СТАРЫЙ МАРШРУТ ОТМЕНЫ ДЛЯ АДМИНКИ
# =========================================================


@app.route("/api/reservations/<int:rid>/cancel", methods=["PATCH"])
@admin_api_required
def cancel(rid):

    connection = db()

    reservation = connection.execute(
        """
        SELECT id, status, user_id
        FROM reservations
        WHERE id = ?
        """,
        (rid,),
    ).fetchone()

    if not reservation:
        connection.close()

        return jsonify(success=False, message="Бронь не найдена."), 404

    connection.execute(
        """
        UPDATE reservations
        SET status = 'cancelled',
            payment_status = CASE WHEN payment_status = 'paid' THEN 'refunded' ELSE payment_status END
        WHERE id = ?
        """,
        (rid,),
    )

    if reservation["status"] != "cancelled":
        add_admin_log(
            connection,
            "reservation_cancelled",
            "reservation",
            rid,
            f"Бронирование #{rid} отменено администратором",
            reservation["status"],
            "cancelled",
        )

    recipient = email_for_user(connection, reservation["user_id"])
    connection.commit()
    connection.close()
    send_booking_email(
        recipient,
        "Отмена бронирования TABLE",
        f"Бронирование №{rid} отменено администратором.",
    )

    return jsonify(success=True)


# =========================================================
# ЖУРНАЛ ДЕЙСТВИЙ АДМИНИСТРАТОРА
# =========================================================


@app.route("/api/admin/logs", methods=["GET"])
@admin_api_required
def admin_logs():
    limit = request.args.get("limit", default=200, type=int)
    limit = max(1, min(limit, 500))

    connection = db()
    rows = connection.execute(
        """
        SELECT id, admin_username, action_type, entity_type, entity_id,
               description, old_value, new_value, created_at
        FROM admin_logs
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    connection.close()

    return jsonify(success=True, logs=[dict(row) for row in rows])


# =========================================================
# МОЯ БРОНЬ — ПОИСК ПО ID И ТЕЛЕФОНУ
# =========================================================


@app.route("/api/my-reservation", methods=["POST"])
def my_reservation():

    data = request.get_json(silent=True) or {}

    try:
        reservation_id = int(data.get("reservation_id"))

    except (TypeError, ValueError):
        return jsonify(success=False, message="Введите корректный номер брони."), 400

    phone = str(data.get("phone", "")).strip()

    if not valid_phone(phone):
        return jsonify(success=False, message="Введите корректный номер телефона."), 400

    entered_phone = normalize_phone(phone)

    connection = db()

    reservation = connection.execute(
        """
        SELECT
            id,
            table_number,
            customer_name,
            phone,
            guests,
            reservation_date,
            reservation_time,
            status,
            special_requests,
            comment,
            preorder_status
        FROM reservations
        WHERE id = ?
        """,
        (reservation_id,),
    ).fetchone()

    connection.close()

    if not reservation:
        return jsonify(success=False, message="Бронирование не найдено."), 404

    saved_phone = normalize_phone(reservation["phone"])

    if saved_phone != entered_phone:
        return jsonify(
            success=False, message="Номер брони или телефон указан неверно."
        ), 404

    reservation_data = dict(reservation)
    connection = db()
    preorder_items, preorder_total = get_reservation_preorder(
        connection, reservation_id
    )
    connection.close()
    reservation_data["preorder_items"] = preorder_items
    reservation_data["preorder_total"] = preorder_total

    return jsonify(success=True, reservation=reservation_data)


# =========================================================
# МОЯ БРОНЬ — ОТМЕНА ПОСЕТИТЕЛЕМ
# =========================================================


@app.route("/api/my-reservation/<int:rid>/cancel", methods=["POST"])
def cancel_my_reservation(rid):

    data = request.get_json(silent=True) or {}

    phone = str(data.get("phone", "")).strip()

    if not valid_phone(phone):
        return jsonify(success=False, message="Введите корректный номер телефона."), 400

    entered_phone = normalize_phone(phone)

    connection = db()

    reservation = connection.execute(
        """
        SELECT
            id,
            phone,
            reservation_date,
            reservation_time,
            status,
            user_id
        FROM reservations
        WHERE id = ?
        """,
        (rid,),
    ).fetchone()

    if not reservation:
        connection.close()

        return jsonify(success=False, message="Бронирование не найдено."), 404

    saved_phone = normalize_phone(reservation["phone"])

    if saved_phone != entered_phone:
        connection.close()

        return jsonify(
            success=False, message="Номер брони или телефон указан неверно."
        ), 403

    if reservation["status"] == "cancelled":
        connection.close()

        return jsonify(success=False, message="Это бронирование уже отменено."), 400

    if reservation["status"] == "completed":
        connection.close()

        return jsonify(
            success=False, message="Завершённое бронирование нельзя отменить."
        ), 400

    if reservation["status"] == "arrived":
        connection.close()

        return jsonify(
            success=False,
            message=("После прибытия гостя бронирование нельзя отменить через сайт."),
        ), 400

    try:
        reservation_datetime = datetime.strptime(
            (f"{reservation['reservation_date']} {reservation['reservation_time']}"),
            "%Y-%m-%d %H:%M",
        )

    except ValueError:
        connection.close()

        return jsonify(success=False, message="Ошибка данных бронирования."), 500

    if reservation_datetime < datetime.now():
        connection.close()

        return jsonify(
            success=False, message="Прошедшее бронирование нельзя отменить."
        ), 400

    connection.execute(
        """
        UPDATE reservations
        SET status = 'cancelled',
            payment_status = CASE WHEN payment_status = 'paid' THEN 'refunded' ELSE payment_status END
        WHERE id = ?
        """,
        (rid,),
    )

    recipient = email_for_user(connection, reservation["user_id"])
    connection.commit()
    connection.close()
    send_booking_email(
        recipient, "Отмена бронирования TABLE", f"Бронирование №{rid} отменено."
    )

    return jsonify(success=True, message="Бронирование успешно отменено.")


# =========================================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# =========================================================

if __name__ == "__main__":
    init_db()

    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
