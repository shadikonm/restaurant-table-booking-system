# ЛЗ 13. Автоматизация отчётности PM

**Проект** — TABLE, система бронирования столиков в ресторане  
**Дисциплина** — IT жобаларды басқару  
**Группа** — АЖ-43

## Цель

Сократить ручной сбор данных о задачах проекта.

## Ход работы

Настроили .github/workflows/pm_weekly.yml. GitHub CLI получает данные из Issues, Python рассчитывает показатели, GitHub Actions публикует weekly-pm-report.zip. Предусмотрели ручной запуск и расписание на понедельник.

## Результат

Подтверждён ручной запуск Weekly PM Report #1 и выгрузка артефакта. Запуск по расписанию отдельно не подтверждён.

## Подтверждающие материалы

GitHub Actions, Weekly PM Report #1, артефакт и журнал проверки.

[Репозиторий TABLE](https://github.com/shadikonm/restaurant-table-booking-system) · [GitHub Project](https://github.com/users/shadikonm/projects/2/views/2)
