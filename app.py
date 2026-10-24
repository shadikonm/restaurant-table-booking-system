from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import re
import os
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "local-development-secret-key"
)

DATABASE = "restaurant.db"

ADMIN_USERNAME = os.environ.get(
    "ADMIN_USERNAME",
    "admin"
)

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    "admin123"
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
    16: 6
}

BOOKING_DURATION_HOURS = 2


# Все допустимые статусы бронирования
ALLOWED_STATUSES = {
    "confirmed",
    "arrived",
    "completed",
    "cancelled"
}


# Только эти статусы блокируют стол
ACTIVE_STATUSES = {
    "confirmed",
    "arrived"
}


ALLOWED_PREORDER_STATUSES = {
    "new",
    "preparing",
    "ready"
}


# =========================================================
# БАЗА ДАННЫХ
# =========================================================

def db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


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
            (table_number, capacity)
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
            ("Тартар из говядины", "Говяжья вырезка, каперсы, корнишоны, дижонская горчица и хрустящий багет", "Закуски", 4200),
            ("Брускетта с ростбифом", "Чиабатта, ростбиф, сливочный крем, руккола и вяленые томаты", "Закуски", 3600),
            ("Креветки в чесночном масле", "Тигровые креветки, чеснок, сливочное масло и свежая зелень", "Закуски", 4900),
            ("Салат с ростбифом", "Ростбиф, микс салатов, томаты черри, пармезан и горчичная заправка", "Салаты", 3900),
            ("Цезарь с курицей", "Куриное филе, романо, пармезан, томаты черри и соус Цезарь", "Салаты", 3400),
            ("Салат с лососем", "Слабосолёный лосось, авокадо, микс салатов и цитрусовая заправка", "Салаты", 4400),
            ("Крем-суп из шампиньонов", "Шампиньоны, сливки, трюфельное масло и хрустящий багет", "Супы", 2900),
            ("Тыквенный крем-суп", "Запечённая тыква, сливки, тыквенные семечки и ароматное масло", "Супы", 2700),
            ("Томлёные говяжьи щёчки", "Говяжьи щёчки длительного томления, картофельное пюре и насыщенный мясной соус", "Горячие блюда", 5900),
            ("Медальоны из телятины", "Телячья вырезка, картофель гратен и сливочно-грибной соус", "Горячие блюда", 6900),
            ("Лосось со сливочным соусом", "Филе лосося, овощи гриль и сливочно-лимонный соус", "Горячие блюда", 6500),
            ("Утиная грудка", "Утиная грудка, ягодный соус и картофельное пюре", "Горячие блюда", 6200),
            ("Куриное филе с грибным соусом", "Куриное филе, картофельное пюре и сливочный соус с шампиньонами", "Горячие блюда", 4500),
            ("Паста с креветками", "Феттучини, тигровые креветки, сливочный соус и пармезан", "Паста", 4900),
            ("Феттучини с грибами", "Паста, шампиньоны, сливочный соус и пармезан", "Паста", 3900),
            ("Карбонара", "Спагетти, бекон, желток и пармезан", "Паста", 4200),
            ("Тирамису", "Классический итальянский десерт с маскарпоне и кофе", "Десерты", 2600),
            ("Баскский чизкейк", "Нежный запечённый чизкейк с карамелизированной корочкой", "Десерты", 2800),
            ("Шоколадный фондан", "Тёплый шоколадный десерт с жидким центром и мороженым", "Десерты", 2900),
            ("Домашний лимонад", "Лимон, лайм, мята и газированная вода", "Напитки", 1800),
            ("Апельсиновый фреш", "Свежевыжатый апельсиновый сок", "Напитки", 2200),
            ("Американо", "Классический чёрный кофе", "Напитки", 1200),
            ("Капучино", "Эспрессо и взбитое молоко", "Напитки", 1600)
        ]
        connection.executemany(
            "INSERT INTO menu_items (name, description, category, price, is_active) VALUES (?, ?, ?, ?, 1)",
            default_menu
        )

    columns = {
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(reservations)"
        ).fetchall()
    }

    if "user_id" not in columns:
        connection.execute(
            "ALTER TABLE reservations ADD COLUMN user_id INTEGER"
        )

    if "payment_status" not in columns:
        connection.execute(
            "ALTER TABLE reservations ADD COLUMN payment_status TEXT NOT NULL DEFAULT 'unpaid'"
        )

    if "payment_method" not in columns:
        connection.execute(
            "ALTER TABLE reservations ADD COLUMN payment_method TEXT"
        )

    if "paid_at" not in columns:
        connection.execute(
            "ALTER TABLE reservations ADD COLUMN paid_at TEXT"
        )

    if "special_requests" not in columns:
        connection.execute(
            "ALTER TABLE reservations ADD COLUMN special_requests TEXT"
        )

    if "comment" not in columns:
        connection.execute(
            "ALTER TABLE reservations ADD COLUMN comment TEXT"
        )

    if "preorder_status" not in columns:
        connection.execute(
            "ALTER TABLE reservations ADD COLUMN preorder_status TEXT"
        )

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
        elif len(password) < 6:
            error = "Пароль должен содержать минимум 6 символов."
        elif password != password2:
            error = "Пароли не совпадают."
        else:
            connection = db()
            existing = connection.execute(
                "SELECT id FROM users WHERE email = ?",
                (email,)
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
                    (name, phone, email, generate_password_hash(password))
                )
                user_id = cursor.lastrowid
                connection.commit()
                connection.close()

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
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        connection.close()

        if not user or not check_password_hash(user["password_hash"], password):
            error = "Неверный email или пароль."
        else:
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

    connection = db()
    user = connection.execute(
        "SELECT id, name, phone, email FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    reservation_rows = connection.execute(
        """
        SELECT id, table_number, customer_name, phone, guests,
               reservation_date, reservation_time, status,
               payment_status, payment_method, paid_at,
               special_requests, comment, preorder_status
        FROM reservations
        WHERE user_id = ?
        ORDER BY reservation_date DESC, reservation_time DESC, id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    reservations = []
    for row in reservation_rows:
        reservation = dict(row)
        preorder_items, preorder_total = get_reservation_preorder(connection, reservation["id"])
        reservation["preorder_items"] = preorder_items
        reservation["preorder_total"] = preorder_total
        reservations.append(reservation)

    connection.close()

    return render_template(
        "account.html",
        user=user,
        reservations=reservations,
        now=datetime.now()
    )


@app.route("/account/reservations/<int:rid>/cancel", methods=["POST"])
@user_required
def account_cancel_reservation(rid):

    connection = db()
    reservation = connection.execute(
        """
        SELECT id, reservation_date, reservation_time, status
        FROM reservations
        WHERE id = ? AND user_id = ?
        """,
        (rid, session["user_id"])
    ).fetchone()

    if not reservation:
        connection.close()
        return redirect(url_for("account"))

    if reservation["status"] != "confirmed":
        connection.close()
        return redirect(url_for("account"))

    try:
        reservation_datetime = datetime.strptime(
            f"{reservation['reservation_date']} {reservation['reservation_time']}",
            "%Y-%m-%d %H:%M"
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
        (rid,)
    )
    connection.commit()
    connection.close()

    return redirect(url_for("account"))


# =========================================================
# DEMO-ОПЛАТА БРОНИРОВАНИЯ
# =========================================================

@app.route("/payment/<int:rid>", methods=["GET", "POST"])
@user_required
def payment(rid):
    connection = db()
    reservation = connection.execute(
        """
        SELECT id, table_number, guests, reservation_date, reservation_time,
               status, payment_status, payment_method, paid_at
        FROM reservations
        WHERE id = ? AND user_id = ?
        """,
        (rid, session["user_id"])
    ).fetchone()

    if not reservation:
        connection.close()
        return redirect(url_for("account"))

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
            return redirect(url_for("account"))
        elif method not in allowed_methods:
            error = "Выберите способ оплаты."
        else:
            paid_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            connection.execute(
                """
                UPDATE reservations
                SET payment_status = 'paid',
                    payment_method = ?,
                    paid_at = ?
                WHERE id = ? AND user_id = ?
                """,
                (method, paid_at, rid, session["user_id"])
            )
            connection.commit()
            connection.close()
            return redirect(url_for("payment_success", rid=rid))

    connection.close()
    return render_template(
        "payment.html",
        reservation=reservation,
        amount=amount,
        error=error
    )


@app.route("/payment/<int:rid>/success")
@user_required
def payment_success(rid):
    connection = db()
    reservation = connection.execute(
        """
        SELECT id, table_number, reservation_date, reservation_time,
               payment_status, payment_method, paid_at
        FROM reservations
        WHERE id = ? AND user_id = ?
        """,
        (rid, session["user_id"])
    ).fetchone()
    connection.close()

    if not reservation or reservation["payment_status"] != "paid":
        return redirect(url_for("account"))

    return render_template(
        "payment_success.html",
        reservation=reservation,
        amount=5000
    )


# =========================================================
# ЗАЩИТА АДМИН-ПАНЕЛИ
# =========================================================

def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not session.get("admin_logged_in"):
            return redirect(
                url_for("admin_login")
            )

        return function(*args, **kwargs)

    return wrapper


def admin_api_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not session.get("admin_logged_in"):

            return jsonify(
                success=False,
                message="Необходим вход администратора."
            ), 401

        return function(*args, **kwargs)

    return wrapper


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================================================

def valid_phone(phone):

    digits = re.sub(
        r"\D",
        "",
        phone
    )

    return 10 <= len(digits) <= 12


def normalize_phone(phone):

    return re.sub(
        r"\D",
        "",
        str(phone)
    )


def normalize_name(name):
    return " ".join(str(name).strip().casefold().split())


def add_admin_log(connection, action_type, entity_type, entity_id, description, old_value=None, new_value=None):
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
            None if new_value is None else str(new_value)
        )
    )


def overlap(time_a, time_b):

    first = datetime.strptime(
        time_a,
        "%H:%M"
    )

    second = datetime.strptime(
        time_b,
        "%H:%M"
    )

    first_end = first + timedelta(
        hours=BOOKING_DURATION_HOURS
    )

    second_end = second + timedelta(
        hours=BOOKING_DURATION_HOURS
    )

    return (
        second < first_end
        and
        first < second_end
    )


def table_is_active(table_number):
    connection = db()
    row = connection.execute(
        "SELECT is_active FROM table_settings WHERE table_number = ?",
        (table_number,)
    ).fetchone()
    connection.close()
    return bool(row["is_active"]) if row is not None else table_number in TABLES


def busy(
    table_number,
    reservation_date,
    reservation_time,
    exclude=None
):

    connection = db()

    sql = """
        SELECT
            id,
            reservation_time
        FROM reservations
        WHERE table_number = ?
        AND reservation_date = ?
        AND status IN ('confirmed', 'arrived')
    """

    params = [
        table_number,
        reservation_date
    ]

    if exclude is not None:

        sql += " AND id != ?"
        params.append(exclude)

    rows = connection.execute(
        sql,
        params
    ).fetchall()

    connection.close()

    return any(
        overlap(
            row["reservation_time"],
            reservation_time
        )
        for row in rows
    )


# =========================================================
# ГЛАВНАЯ СТРАНИЦА
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# ВХОД АДМИНИСТРАТОРА
# =========================================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if session.get("admin_logged_in"):

        return redirect(
            url_for("admin")
        )

    error = None

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if (
            username == ADMIN_USERNAME
            and
            password == ADMIN_PASSWORD
        ):

            session.clear()

            session["admin_logged_in"] = True

            session["admin_username"] = ADMIN_USERNAME

            return redirect(
                url_for("admin")
            )

        error = "Неверный логин или пароль."

    return render_template(
        "login.html",
        error=error
    )


@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(
        url_for("admin_login")
    )


@app.route("/admin")
@admin_required
def admin():

    return render_template(
        "admin.html",
        admin_username=session.get(
            "admin_username",
            "admin"
        )
    )


# =========================================================
# ПРОВЕРКА ДОСТУПНОСТИ СТОЛОВ
# =========================================================

@app.route("/api/availability")
def availability():

    date = request.args.get(
        "date",
        ""
    )

    time = request.args.get(
        "time",
        ""
    )

    guests = request.args.get(
        "guests",
        type=int
    )

    if not date or not time or not guests:

        return jsonify(
            success=False,
            message="Выберите дату, время и количество гостей."
        ), 400

    try:

        reservation_datetime = datetime.strptime(
            f"{date} {time}",
            "%Y-%m-%d %H:%M"
        )

    except ValueError:

        return jsonify(
            success=False,
            message="Некорректная дата или время."
        ), 400

    if reservation_datetime < datetime.now():

        return jsonify(
            success=False,
            message="Нельзя выбрать прошедшее время."
        ), 400

    unsuitable_tables = [
        table_number
        for table_number, capacity in TABLES.items()
        if capacity < guests
    ]

    disabled_tables = [
        table_number for table_number in TABLES
        if not table_is_active(table_number)
    ]

    busy_tables = [
        table_number
        for table_number, capacity in TABLES.items()
        if capacity >= guests and (
            table_number in disabled_tables
            or busy(table_number, date, time)
        )
    ]

    return jsonify(
        success=True,
        busy_tables=busy_tables,
        unsuitable_tables=unsuitable_tables,
        disabled_tables=disabled_tables
    )


# =========================================================
# СОЗДАНИЕ НОВОЙ БРОНИ
# =========================================================

@app.route(
    "/api/reservations",
    methods=["POST"]
)
def create_reservation():

    data = request.get_json(
        silent=True
    ) or {}

    name = str(
        data.get(
            "customer_name",
            ""
        )
    ).strip()

    phone = str(
        data.get(
            "phone",
            ""
        )
    ).strip()

    raw_special_requests = data.get("special_requests", [])
    if not isinstance(raw_special_requests, list):
        raw_special_requests = []

    allowed_special_requests = {
        "window", "child_chair", "birthday", "quiet", "accessible"
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
            return jsonify(success=False, message="Количество одного блюда должно быть от 1 до 20."), 400
        preorder_quantities[menu_item_id] = preorder_quantities.get(menu_item_id, 0) + quantity

    date = str(
        data.get(
            "reservation_date",
            ""
        )
    ).strip()

    time = str(
        data.get(
            "reservation_time",
            ""
        )
    ).strip()

    try:

        table = int(
            data.get(
                "table_number"
            )
        )

        guests = int(
            data.get(
                "guests"
            )
        )

    except (TypeError, ValueError):

        return jsonify(
            success=False,
            message="Некорректные данные."
        ), 400

    if not 2 <= len(name) <= 50:

        return jsonify(
            success=False,
            message="Введите корректное имя."
        ), 400

    if not valid_phone(phone):

        return jsonify(
            success=False,
            message="Введите корректный телефон."
        ), 400

    if (
        table not in TABLES
        or
        guests < 1
        or
        guests > TABLES[table]
    ):

        return jsonify(
            success=False,
            message="Стол не подходит для этого количества гостей."
        ), 400

    if not table_is_active(table):
        return jsonify(success=False, message="Этот стол временно недоступен для бронирования."), 409

    try:

        reservation_datetime = datetime.strptime(
            f"{date} {time}",
            "%Y-%m-%d %H:%M"
        )

    except ValueError:

        return jsonify(
            success=False,
            message="Некорректная дата или время."
        ), 400

    if reservation_datetime < datetime.now():

        return jsonify(
            success=False,
            message="Нельзя бронировать прошедшее время."
        ), 400

    if busy(
        table,
        date,
        time
    ):

        return jsonify(
            success=False,
            message="Этот стол уже занят на выбранный период."
        ), 409

    connection = db()

    reservation_user_id = None
    logged_in_user_id = session.get("user_id")

    if logged_in_user_id:
        logged_in_user = connection.execute(
            "SELECT id, name, phone FROM users WHERE id = ?",
            (logged_in_user_id,)
        ).fetchone()

        if (
            logged_in_user
            and normalize_name(logged_in_user["name"]) == normalize_name(name)
            and normalize_phone(logged_in_user["phone"]) == normalize_phone(phone)
        ):
            reservation_user_id = logged_in_user["id"]

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
            comment
        )
        VALUES (?, ?, ?, ?, ?, ?, 'confirmed', ?, ?, ?)
        """,
        (
            table,
            name,
            phone,
            guests,
            date,
            time,
            reservation_user_id,
            special_requests_text,
            comment
        )
    )

    reservation_id = cursor.lastrowid
    preorder_total = 0

    if preorder_quantities:
        menu_ids = list(preorder_quantities.keys())
        placeholders = ",".join("?" for _ in menu_ids)
        menu_rows = connection.execute(
            f"SELECT id, price FROM menu_items WHERE is_active = 1 AND id IN ({placeholders})",
            menu_ids
        ).fetchall()
        menu_by_id = {row["id"]: row for row in menu_rows}

        if len(menu_by_id) != len(menu_ids):
            connection.rollback()
            connection.close()
            return jsonify(success=False, message="Одно из выбранных блюд больше недоступно."), 400

        for menu_item_id, quantity in preorder_quantities.items():
            unit_price = menu_by_id[menu_item_id]["price"]
            preorder_total += unit_price * quantity
            connection.execute(
                """
                INSERT INTO reservation_items (reservation_id, menu_item_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
                """,
                (reservation_id, menu_item_id, quantity, unit_price)
            )

        connection.execute(
            "UPDATE reservations SET preorder_status = 'new' WHERE id = ?",
            (reservation_id,)
        )

    connection.commit()
    connection.close()

    return jsonify(
        success=True,
        reservation_id=reservation_id,
        preorder_total=preorder_total
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
        (reservation_id,)
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
    return jsonify(success=True, tables=[
        {"table_number": row["table_number"], "capacity": row["capacity"], "is_active": bool(row["is_active"])}
        for row in rows
    ])


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
        "SELECT is_active FROM table_settings WHERE table_number = ?",
        (table_number,)
    ).fetchone()
    old_active = bool(current["is_active"]) if current else True

    connection.execute(
        "INSERT INTO table_settings (table_number, capacity, is_active) VALUES (?, ?, ?) "
        "ON CONFLICT(table_number) DO UPDATE SET capacity = excluded.capacity, is_active = excluded.is_active",
        (table_number, TABLES[table_number], 1 if is_active else 0)
    )

    if old_active != is_active:
        add_admin_log(
            connection,
            "table_status_changed",
            "table",
            table_number,
            f"Стол №{table_number}: {'включён' if is_active else 'отключён'}",
            "active" if old_active else "inactive",
            "active" if is_active else "inactive"
        )

    connection.commit()
    connection.close()
    return jsonify(success=True, table_number=table_number, is_active=is_active)


# =========================================================
# ПОЛУЧЕНИЕ ВСЕХ БРОНЕЙ ДЛЯ АДМИНА
# =========================================================

@app.route(
    "/api/reservations",
    methods=["GET"]
)
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
        preorder_items, preorder_total = get_reservation_preorder(connection, reservation["id"])
        reservation["preorder_items"] = preorder_items
        reservation["preorder_total"] = preorder_total
        reservations.append(reservation)

    connection.close()

    return jsonify(
        success=True,
        reservations=reservations
    )


# =========================================================
# РЕДАКТИРОВАНИЕ БРОНИ АДМИНИСТРАТОРОМ
# =========================================================

@app.route(
    "/api/reservations/<int:rid>",
    methods=["PUT"]
)
@admin_api_required
def update_reservation(rid):

    data = request.get_json(
        silent=True
    ) or {}

    name = str(
        data.get(
            "customer_name",
            ""
        )
    ).strip()

    phone = str(
        data.get(
            "phone",
            ""
        )
    ).strip()

    date = str(
        data.get(
            "reservation_date",
            ""
        )
    ).strip()

    time = str(
        data.get(
            "reservation_time",
            ""
        )
    ).strip()

    try:

        table = int(
            data.get(
                "table_number"
            )
        )

        guests = int(
            data.get(
                "guests"
            )
        )

    except (TypeError, ValueError):

        return jsonify(
            success=False,
            message="Некорректные данные."
        ), 400

    if (
        not 2 <= len(name) <= 50
        or
        not valid_phone(phone)
    ):

        return jsonify(
            success=False,
            message="Проверьте имя и телефон."
        ), 400

    if (
        table not in TABLES
        or
        guests < 1
        or
        guests > TABLES[table]
    ):

        return jsonify(
            success=False,
            message="Стол не подходит для этого количества гостей."
        ), 400

    if not table_is_active(table):
        return jsonify(success=False, message="Этот стол временно отключён администратором."), 409

    try:

        datetime.strptime(
            f"{date} {time}",
            "%Y-%m-%d %H:%M"
        )

    except ValueError:

        return jsonify(
            success=False,
            message="Некорректная дата или время."
        ), 400

    connection = db()

    reservation = connection.execute(
        """
        SELECT
            id, table_number, customer_name, phone, guests,
            reservation_date, reservation_time, status
        FROM reservations
        WHERE id = ?
        """,
        (rid,)
    ).fetchone()

    connection.close()

    if not reservation:

        return jsonify(
            success=False,
            message="Бронь не найдена."
        ), 404

    if reservation["status"] in {
        "completed",
        "cancelled"
    }:

        return jsonify(
            success=False,
            message="Завершённую или отменённую бронь нельзя редактировать."
        ), 400

    if busy(
        table,
        date,
        time,
        rid
    ):

        return jsonify(
            success=False,
            message="Стол уже занят."
        ), 409

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
        (
            table,
            name,
            phone,
            guests,
            date,
            time,
            rid
        )
    )

    old_summary = (
        f"Стол {reservation['table_number']}; {reservation['customer_name']}; "
        f"{reservation['phone']}; гостей {reservation['guests']}; "
        f"{reservation['reservation_date']} {reservation['reservation_time']}"
    )
    new_summary = (
        f"Стол {table}; {name}; {phone}; гостей {guests}; {date} {time}"
    )

    if old_summary != new_summary:
        add_admin_log(
            connection,
            "reservation_edited",
            "reservation",
            rid,
            f"Отредактировано бронирование #{rid}",
            old_summary,
            new_summary
        )

    connection.commit()
    connection.close()

    return jsonify(
        success=True
    )


# =========================================================
# ИЗМЕНЕНИЕ СТАТУСА АДМИНИСТРАТОРОМ
# =========================================================

@app.route(
    "/api/reservations/<int:rid>/status",
    methods=["PATCH"]
)
@admin_api_required
def update_reservation_status(rid):

    data = request.get_json(
        silent=True
    ) or {}

    new_status = str(
        data.get(
            "status",
            ""
        )
    ).strip()

    if new_status not in ALLOWED_STATUSES:

        return jsonify(
            success=False,
            message="Недопустимый статус."
        ), 400

    connection = db()

    reservation = connection.execute(
        """
        SELECT *
        FROM reservations
        WHERE id = ?
        """,
        (rid,)
    ).fetchone()

    connection.close()

    if not reservation:

        return jsonify(
            success=False,
            message="Бронь не найдена."
        ), 404

    if new_status in ACTIVE_STATUSES:

        if busy(
            reservation["table_number"],
            reservation["reservation_date"],
            reservation["reservation_time"],
            rid
        ):

            return jsonify(
                success=False,
                message=(
                    "Нельзя активировать бронь: "
                    "стол уже занят другим бронированием."
                )
            ), 409

    connection = db()

    connection.execute(
        """
        UPDATE reservations
        SET status = ?
        WHERE id = ?
        """,
        (
            new_status,
            rid
        )
    )

    if reservation["status"] != new_status:
        add_admin_log(
            connection,
            "reservation_status_changed",
            "reservation",
            rid,
            f"Изменён статус бронирования #{rid}",
            reservation["status"],
            new_status
        )

    connection.commit()
    connection.close()

    return jsonify(
        success=True
    )


# =========================================================
# ИЗМЕНЕНИЕ СТАТУСА ПРЕДЗАКАЗА АДМИНИСТРАТОРОМ
# =========================================================

@app.route(
    "/api/admin/reservations/<int:rid>/preorder-status",
    methods=["PATCH"]
)
@admin_api_required
def update_preorder_status(rid):

    data = request.get_json(silent=True) or {}
    new_status = str(data.get("status", "")).strip()

    if new_status not in ALLOWED_PREORDER_STATUSES:
        return jsonify(success=False, message="Недопустимый статус предзаказа."), 400

    connection = db()
    reservation = connection.execute(
        "SELECT id, preorder_status FROM reservations WHERE id = ?",
        (rid,)
    ).fetchone()

    if not reservation:
        connection.close()
        return jsonify(success=False, message="Бронирование не найдено."), 404

    preorder_exists = connection.execute(
        "SELECT id FROM reservation_items WHERE reservation_id = ? LIMIT 1",
        (rid,)
    ).fetchone()

    if not preorder_exists:
        connection.close()
        return jsonify(success=False, message="У этой брони нет предзаказа."), 400

    connection.execute(
        "UPDATE reservations SET preorder_status = ? WHERE id = ?",
        (new_status, rid)
    )

    if reservation["preorder_status"] != new_status:
        add_admin_log(
            connection,
            "preorder_status_changed",
            "reservation",
            rid,
            f"Изменён статус предзаказа для бронирования #{rid}",
            reservation["preorder_status"],
            new_status
        )

    connection.commit()
    connection.close()

    return jsonify(success=True, preorder_status=new_status)


# =========================================================
# СТАРЫЙ МАРШРУТ ОТМЕНЫ ДЛЯ АДМИНКИ
# =========================================================

@app.route(
    "/api/reservations/<int:rid>/cancel",
    methods=["PATCH"]
)
@admin_api_required
def cancel(rid):

    connection = db()

    reservation = connection.execute(
        """
        SELECT id, status
        FROM reservations
        WHERE id = ?
        """,
        (rid,)
    ).fetchone()

    if not reservation:

        connection.close()

        return jsonify(
            success=False,
            message="Бронь не найдена."
        ), 404

    connection.execute(
        """
        UPDATE reservations
        SET status = 'cancelled',
            payment_status = CASE WHEN payment_status = 'paid' THEN 'refunded' ELSE payment_status END
        WHERE id = ?
        """,
        (rid,)
    )

    if reservation["status"] != "cancelled":
        add_admin_log(
            connection,
            "reservation_cancelled",
            "reservation",
            rid,
            f"Бронирование #{rid} отменено администратором",
            reservation["status"],
            "cancelled"
        )

    connection.commit()
    connection.close()

    return jsonify(
        success=True
    )


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
        (limit,)
    ).fetchall()
    connection.close()

    return jsonify(success=True, logs=[dict(row) for row in rows])


# =========================================================
# МОЯ БРОНЬ — ПОИСК ПО ID И ТЕЛЕФОНУ
# =========================================================

@app.route(
    "/api/my-reservation",
    methods=["POST"]
)
def my_reservation():

    data = request.get_json(
        silent=True
    ) or {}

    try:

        reservation_id = int(
            data.get(
                "reservation_id"
            )
        )

    except (TypeError, ValueError):

        return jsonify(
            success=False,
            message="Введите корректный номер брони."
        ), 400

    phone = str(
        data.get(
            "phone",
            ""
        )
    ).strip()

    if not valid_phone(phone):

        return jsonify(
            success=False,
            message="Введите корректный номер телефона."
        ), 400

    entered_phone = normalize_phone(
        phone
    )

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
        (reservation_id,)
    ).fetchone()

    connection.close()

    if not reservation:

        return jsonify(
            success=False,
            message="Бронирование не найдено."
        ), 404

    saved_phone = normalize_phone(
        reservation["phone"]
    )

    if saved_phone != entered_phone:

        return jsonify(
            success=False,
            message="Номер брони или телефон указан неверно."
        ), 404

    reservation_data = dict(reservation)
    connection = db()
    preorder_items, preorder_total = get_reservation_preorder(connection, reservation_id)
    connection.close()
    reservation_data["preorder_items"] = preorder_items
    reservation_data["preorder_total"] = preorder_total

    return jsonify(
        success=True,
        reservation=reservation_data
    )


# =========================================================
# МОЯ БРОНЬ — ОТМЕНА ПОСЕТИТЕЛЕМ
# =========================================================

@app.route(
    "/api/my-reservation/<int:rid>/cancel",
    methods=["POST"]
)
def cancel_my_reservation(rid):

    data = request.get_json(
        silent=True
    ) or {}

    phone = str(
        data.get(
            "phone",
            ""
        )
    ).strip()

    if not valid_phone(phone):

        return jsonify(
            success=False,
            message="Введите корректный номер телефона."
        ), 400

    entered_phone = normalize_phone(
        phone
    )

    connection = db()

    reservation = connection.execute(
        """
        SELECT
            id,
            phone,
            reservation_date,
            reservation_time,
            status
        FROM reservations
        WHERE id = ?
        """,
        (rid,)
    ).fetchone()

    if not reservation:

        connection.close()

        return jsonify(
            success=False,
            message="Бронирование не найдено."
        ), 404

    saved_phone = normalize_phone(
        reservation["phone"]
    )

    if saved_phone != entered_phone:

        connection.close()

        return jsonify(
            success=False,
            message="Номер брони или телефон указан неверно."
        ), 403

    if reservation["status"] == "cancelled":

        connection.close()

        return jsonify(
            success=False,
            message="Это бронирование уже отменено."
        ), 400

    if reservation["status"] == "completed":

        connection.close()

        return jsonify(
            success=False,
            message="Завершённое бронирование нельзя отменить."
        ), 400

    if reservation["status"] == "arrived":

        connection.close()

        return jsonify(
            success=False,
            message=(
                "После прибытия гостя бронирование "
                "нельзя отменить через сайт."
            )
        ), 400

    try:

        reservation_datetime = datetime.strptime(
            (
                f"{reservation['reservation_date']} "
                f"{reservation['reservation_time']}"
            ),
            "%Y-%m-%d %H:%M"
        )

    except ValueError:

        connection.close()

        return jsonify(
            success=False,
            message="Ошибка данных бронирования."
        ), 500

    if reservation_datetime < datetime.now():

        connection.close()

        return jsonify(
            success=False,
            message="Прошедшее бронирование нельзя отменить."
        ), 400

    connection.execute(
        """
        UPDATE reservations
        SET status = 'cancelled',
            payment_status = CASE WHEN payment_status = 'paid' THEN 'refunded' ELSE payment_status END
        WHERE id = ?
        """,
        (rid,)
    )

    connection.commit()
    connection.close()

    return jsonify(
        success=True,
        message="Бронирование успешно отменено."
    )


# =========================================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# =========================================================

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )