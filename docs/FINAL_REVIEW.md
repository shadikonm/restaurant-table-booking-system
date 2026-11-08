# Проверка текущей версии

27 pytest PASS; Ruff E4/E7/E9/F PASS; 321 запись словаря без пустых переводов; pip-audit без известных уязвимостей.

GitHub CI для commit 4ba9be9a2ef694f96b889c4cff5f0a6522f91dbb:
- https://github.com/shadikonm/restaurant-table-booking-system/actions/runs/42501348701 — success
- https://github.com/shadikonm/restaurant-table-booking-system/actions/runs/42501344369 — success

PR: https://github.com/shadikonm/restaurant-table-booking-system/pull/48 — merged.

Нагрузка: 200 пользователей, 600 запросов чтения, 0 ошибок, p95 4143,88 мс. Цель 2 с не достигнута. Браузерная и независимая приёмка не заменяются этими результатами.
