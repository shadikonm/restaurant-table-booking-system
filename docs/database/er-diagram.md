# ER-диаграмма базы данных

## Система бронирования столиков ресторана

ER-диаграмма отражает основные сущности текущей реализации базы данных и связь между ними.

```mermaid
erDiagram

    USERS ||--o{ RESERVATIONS : "создает"

    USERS {
        INTEGER id PK
        TEXT name
        TEXT phone
        TEXT email UK
        TEXT password_hash
        TEXT created_at
    }

    RESERVATIONS {
        INTEGER id PK
        INTEGER table_number
        TEXT customer_name
        TEXT phone
        INTEGER guests
        TEXT reservation_date
        TEXT reservation_time
        TEXT status
        INTEGER user_id FK
        TEXT payment_status
        TEXT payment_method
        TEXT paid_at
    }
```

## Описание связи

Связь между сущностями:

`USERS 1 : N RESERVATIONS`

Один зарегистрированный пользователь может иметь несколько бронирований.

Поле `RESERVATIONS.user_id` логически связано с `USERS.id`.

При этом `user_id` является необязательным, поскольку бронирование может быть создано посетителем без регистрации.

## Обозначения

- `PK` — Primary Key, первичный ключ;
- `FK` — Foreign Key, внешний ключ;
- `UK` — Unique Key, уникальное значение;
- `1:N` — связь «один ко многим».
