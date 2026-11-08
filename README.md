# TABLE

Веб-система бронирования одного ресторана: Python 3.12+, Flask, Jinja2, SQLite, HTML/CSS/JavaScript. 10 столов в зале, 6 на террасе.

## Запуск на Mac

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD="$(python -c 'import getpass; print(getpass.getpass("Пароль администратора: "))')"
python app.py
```

Откройте http://127.0.0.1:5000. Пустая база создаётся автоматически. Общего встроенного пароля администратора нет. Debug выключен.

## Функции

Регистрация, вход, схема столов, доступность, бронирование, предзаказ, кабинет, отмена, админ-панель, журнал, помощник и демонстрационная предоплата.

Предоплата 5000 ₸: >4 гостей; любой предзаказ; 4 гостя за столом на 6; 1–2 гостя за столом вместимостью >2. До оплаты pending_payment, резерв 15 минут. Продолжение оплаты в кабинете. Реального списания денег нет. Параллельные пересечения запрещены триггерами SQLite; администратор не может подтвердить неоплаченную обязательную предоплату.

## Проверки

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -v
python -m ruff check app.py assistant_service.py db_integrity.py maintenance.py monitor.py tests scripts --select E4,E7,E9,F
python -m pip_audit -r requirements.txt
```

[Лабораторные 1–15](labs/README.md) · [ADR](docs/adr/README.md) · [Демонстрация](docs/DEMO_SCRIPT.md).

## Эксплуатация и ограничения

`python maintenance.py backup` создаёт SQLite backup. Восстановление после остановки сайта: `python maintenance.py restore ПУТЬ`. SMTP требует настройки; без неё доставка писем не заявляется.

`docker compose up -d` запускает Uptime Kuma на порту 3001. Добавьте monitor `http://host.docker.internal:5000/health`. Конфигурация не доказывает уже проведённый мониторинг.

Не публикуйте .env, клиентскую базу, копии и логи. Классификатор Ollama ЛЗ 12 — отдельный эксперимент; FAQ сайта не приравнивается к нему. Production-запуск не заявлен. До него необходимы утверждение политики данных, HTTPS и эксплуатационный сервер. Остаток действий: [реестр](labs/REMAINING_ACTIONS.md).
