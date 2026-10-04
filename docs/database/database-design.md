# Проектирование базы данных

## 1. СУБД

В проекте используется SQLite.

Файл базы данных:

`restaurant.db`

База данных используется для хранения пользователей и бронирований ресторана.

---

# 2. Таблица users

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
