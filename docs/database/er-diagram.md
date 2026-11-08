# Связи текущей модели данных

```mermaid
erDiagram
    USERS ||--o{ RESERVATIONS : owns
    TABLE_SETTINGS ||--o{ RESERVATIONS : identifies
    RESERVATIONS ||--o{ RESERVATION_ITEMS : contains
    MENU_ITEMS ||--o{ RESERVATION_ITEMS : references
    RESERVATIONS ||--o{ EMAIL_REMINDERS : schedules
```

Связи users и table_settings с reservations логические: исходная SQLite-схема не объявляет для них FOREIGN KEY. Связь reservation_items объявлена в DDL. Наличие DDL само по себе не доказывает включение PRAGMA foreign_keys на каждом соединении. admin_logs хранит административные события. Полный перечень полей — data-structure.md.
