# Текущая база TABLE

SQLite restaurant.db, создаётся init_db. Основные таблицы: users, reservations, table_settings, menu_items, reservation_items, admin_logs, email_reminders. Связи:user→reservations;reservation→reservation_items→menu_items. PostgreSQL был исходным планом, изменение зафиксированоADR-002. Пересечения активных броней и переходы обязательной оплаты контролируют триггерыdb_integrity.py. База и backups не публикуются.
