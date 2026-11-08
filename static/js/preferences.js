(() => {
  "use strict";
  const dictionary = {"Главная":["Басты бет","Home"],"Бронирование":["Брондау","Reservation"],"Бронирования":["Брондаулар","Reservations"],"Схема ресторана":["Мейрамхана жоспары","Restaurant layout"],"Моя бронь":["Менің брондауым","My reservation"],"Личный кабинет":["Жеке кабинет","My account"],"Войти":["Кіру","Sign in"],"Регистрация":["Тіркелу","Registration"],"На сайт":["Сайтқа өту","Back to site"],"Выйти":["Шығу","Sign out"],"ОНЛАЙН-БРОНИРОВАНИЕ":["ОНЛАЙН БРОНДАУ","ONLINE RESERVATIONS"],"Ваш стол уже ждёт":["Үстеліңіз сізді күтіп тұр","Your table is waiting"],"Выберите дату, время и количество гостей. Затем выберите стол в основном зале или на террасе.":["Күнді, уақытты және қонақтар санын таңдаңыз. Содан кейін залдан немесе террасадан үстел таңдаңыз.","Choose a date, time and party size. Then select a table in the main hall or on the terrace."],"Выбрать стол":["Үстел таңдау","Choose a table"],"Дата":["Күні","Date"],"Время":["Уақыты","Time"],"Выберите время":["Уақытты таңдаңыз","Select a time"],"Гостей":["Қонақ саны","Guests"],"Показать столы":["Үстелдерді көрсету","Show tables"],"СХЕМА РЕСТОРАНА":["МЕЙРАМХАНА ЖОСПАРЫ","RESTAURANT LAYOUT"],"Выберите столик":["Үстелді таңдаңыз","Choose a table"],"Переключайтесь между основным залом и террасой.":["Негізгі зал мен терраса арасында ауысыңыз.","Switch between the main hall and terrace."],"Свободен":["Бос","Available"],"Занят":["Бос емес","Occupied"],"Не подходит":["Сәйкес емес","Not suitable"],"Зал":["Зал","Hall"],"Терраса":["Терраса","Terrace"],"10 столов":["10 үстел","10 tables"],"6 столов":["6 үстел","6 tables"],"ОСНОВНОЙ ЗАЛ":["НЕГІЗГІ ЗАЛ","MAIN HALL"],"ОКНА":["ТЕРЕЗЕЛЕР","WINDOWS"],"ДЕТСКАЯ ЗОНА":["БАЛАЛАР АЙМАҒЫ","KIDS AREA"],"игровая зона":["ойын аймағы","play area"],"БАР":["БАР","BAR"],"ВХОД":["КІРЕБЕРІС","ENTRANCE"],"2 места":["2 орын","2 seats"],"4 места":["4 орын","4 seats"],"6 мест":["6 орын","6 seats"],"ТЕРРАСА":["ТЕРРАСА","TERRACE"],"ОТКРЫТАЯ ТЕРРАСА":["АШЫҚ ТЕРРАСА","OPEN TERRACE"],"ХАРАКТЕРИСТИКИ":["ЕРЕКШЕЛІКТЕР","FEATURES"],"🪟 У окна":["🪟 Терезе жанында","🪟 By the window"],"🔇 Тихая зона":["🔇 Тыныш аймақ","🔇 Quiet area"],"👶 Рядом с детской зоной":["👶 Балалар аймағына жақын","👶 Near the kids area"],"♿ Доступный стол":["♿ Қолжетімді үстел","♿ Accessible table"],"🌿 Терраса":["🌿 Терраса","🌿 Terrace"],"БРОНИРОВАНИЕ":["БРОНДАУ","RESERVATION"],"Стол №":["Үстел №","Table No."],"Зона":["Аймақ","Area"],"Особенности":["Ерекшеліктер","Features"],"Имя":["Аты","Name"],"Телефон":["Телефон","Phone"],"ПРЕДЗАКАЗ БЛЮД":["ТАҒАМҒА АЛДЫН АЛА ТАПСЫРЫС","MEAL PREORDER"],"Предзаказ блюд":["Тағамға алдын ала тапсырыс","Meal preorder"],"Можно выбрать блюда заранее. Оплата брони 5 000 ₸ остаётся отдельной.":["Тағамдарды алдын ала таңдауға болады. 5 000 ₸ брондау төлемі бөлек төленеді.","You can select dishes in advance. The 5,000 ₸ reservation payment is separate."],"Загружаем меню...":["Мәзір жүктелуде...","Loading menu..."],"ОСОБЫЕ ПОЖЕЛАНИЯ":["АРНАЙЫ ТІЛЕКТЕР","SPECIAL REQUESTS"],"Особые пожелания":["Арнайы тілектер","Special requests"],"🪟 Столик у окна":["🪟 Терезе жанындағы үстел","🪟 Window table"],"👶 Детский стул":["👶 Балалар орындығы","👶 High chair"],"🎂 День рождения":["🎂 Туған күн","🎂 Birthday"],"🔇 Тихое место":["🔇 Тыныш орын","🔇 Quiet spot"],"Комментарий к бронированию":["Брондауға түсініктеме","Reservation comment"],"Подтвердить бронирование":["Брондауды растау","Confirm reservation"],"БРОНИРОВАНИЕ СОЗДАНО":["БРОНДАУ ЖАСАЛДЫ","RESERVATION CREATED"],"Стол забронирован":["Үстел брондалды","Table reserved"],"Номер брони":["Брондау нөмірі","Reservation number"],"Стол":["Үстел","Table"],"Сохраните номер брони. Он понадобится, чтобы посмотреть или отменить бронирование.":["Брондау нөмірін сақтаңыз. Ол брондауды көру немесе болдырмау үшін қажет.","Keep your reservation number to view or cancel your booking."],"Готово":["Дайын","Done"],"МОЯ БРОНЬ":["МЕНІҢ БРОНДАУЫМ","MY RESERVATION"],"Найти бронирование":["Брондауды табу","Find reservation"],"Введите номер брони и телефон, который был указан при бронировании.":["Брондау нөмірін және брондау кезінде көрсетілген телефонды енгізіңіз.","Enter the reservation number and the phone number used for booking."],"Бронирование №":["Брондау №","Reservation No."],"Статус":["Мәртебе","Status"],"Отменить бронирование":["Брондауды болдырмау","Cancel reservation"],"Назад":["Артқа","Back"],"Система онлайн-бронирования столиков":["Үстелдерді онлайн брондау жүйесі","Online table reservation system"],"ЛИЧНЫЙ КАБИНЕТ":["ЖЕКЕ КАБИНЕТ","MY ACCOUNT"],"Здесь находятся ваши бронирования и информация об оплате.":["Мұнда брондауларыңыз бен төлем туралы ақпарат бар.","Your reservations and payment information are here."],"МОИ БРОНИ":["МЕНІҢ БРОНДАУЛАРЫМ","MY BOOKINGS"],"+ Новая бронь":["+ Жаңа брондау","+ New reservation"],"ОПЛАТА":["ТӨЛЕМ","PAYMENT"],"Оплачено":["Төленді","Paid"],"Возврат":["Қайтарылды","Refunded"],"Не оплачено":["Төленбеген","Unpaid"],"Сумма":["Сома","Amount"],"Демо-платёж подтверждён":["Демо төлем расталды","Demo payment confirmed"],"Бронирование отменено. Платёж отмечен как возвращённый.":["Брондау болдырылмады. Төлем қайтарылған деп белгіленді.","Reservation cancelled. Payment marked as refunded."],"Вы можете оплатить бронирование в демонстрационном режиме.":["Брондауды демо режимде төлей аласыз.","You can pay for the reservation in demo mode."],"Оплатить бронь — 5 000 ₸":["Брондауды төлеу — 5 000 ₸","Pay reservation — 5,000 ₸"],"У вас пока нет бронирований":["Әзірге брондауларыңыз жоқ","You have no reservations yet"],"Выберите дату, время и столик на главной странице.":["Басты беттен күнді, уақытты және үстелді таңдаңыз.","Choose a date, time and table on the home page."],"Забронировать столик":["Үстел брондау","Reserve a table"],"Создайте аккаунт, чтобы новые бронирования автоматически сохранялись в личном кабинете.":["Жаңа брондаулар жеке кабинетте автоматты түрде сақталуы үшін тіркеліңіз.","Create an account to save new reservations automatically."],"Создать аккаунт":["Аккаунт ашу","Create account"],"ИМЯ":["АТЫ","NAME"],"ТЕЛЕФОН":["ТЕЛЕФОН","PHONE"],"ПАРОЛЬ":["ҚҰПИЯСӨЗ","PASSWORD"],"ПОВТОР ПАРОЛЯ":["ҚҰПИЯСӨЗДІ ҚАЙТАЛАҢЫЗ","REPEAT PASSWORD"],"Пароль":["Құпиясөз","Password"],"Повторите пароль":["Құпиясөзді қайталаңыз","Repeat password"],"Зарегистрироваться":["Тіркелу","Register"],"Уже есть аккаунт?":["Аккаунтыңыз бар ма?","Already have an account?"],"Вход":["Кіру","Sign in"],"Войдите, чтобы посмотреть бронирования, связанные с вашим аккаунтом.":["Аккаунтыңызға байланысты брондауларды көру үшін кіріңіз.","Sign in to view reservations linked to your account."],"Войти в аккаунт":["Аккаунтқа кіру","Sign in to account"],"Нет аккаунта?":["Аккаунтыңыз жоқ па?","Don't have an account?"],"Вход администратора":["Әкімшіге кіру","Administrator sign in"],"Войдите, чтобы управлять бронированиями, столиками и отчётами ресторана.":["Мейрамхананың брондауларын, үстелдерін және есептерін басқару үшін кіріңіз.","Sign in to manage restaurant reservations, tables and reports."],"Логин":["Логин","Username"],"← Вернуться на сайт":["← Сайтқа оралу","← Return to site"],"Оплата бронирования":["Брондау төлемі","Reservation payment"],"Учебный режим. Настоящие деньги не списываются, данные банковской карты не запрашиваются и не сохраняются.":["Демо режим. Нақты ақша алынбайды, банк картасының деректері сұралмайды және сақталмайды.","Demo mode. No real money is charged and no card details are requested or stored."],"К оплате":["Төленетін сома","Amount due"],"Способ оплаты":["Төлем әдісі","Payment method"],"Банковская карта":["Банк картасы","Bank card"],"Демо-оплата без ввода реквизитов":["Деректерді енгізусіз демо төлем","Demo payment without card details"],"Имитация подтверждения QR-платежа":["QR төлемін растау үлгісі","Simulated QR payment confirmation"],"Имитация бесконтактной оплаты":["Контактісіз төлем үлгісі","Simulated contactless payment"],"Подтвердить демо-оплату":["Демо төлемді растау","Confirm demo payment"],"ПЛАТЁЖ ПОДТВЕРЖДЁН":["ТӨЛЕМ РАСТАЛДЫ","PAYMENT CONFIRMED"],"Бронь оплачена":["Брондау төленді","Reservation paid"],"Это демонстрационный платёж для учебного проекта. Реального списания средств не было.":["Бұл демо төлем. Нақты ақша алынған жоқ.","This is a demo payment. No actual charge was made."],"Вернуться в личный кабинет":["Жеке кабинетке оралу","Return to account"],"Дашборд":["Басқару тақтасы","Dashboard"],"Столики":["Үстелдер","Tables"],"Отчёты":["Есептер","Reports"],"Предзаказы":["Алдын ала тапсырыстар","Preorders"],"Журнал действий":["Әрекеттер журналы","Activity log"],"ДАШБОРД":["БАСҚАРУ ТАҚТАСЫ","DASHBOARD"],"ОБЗОР РЕСТОРАНА":["МЕЙРАМХАНА ШОЛУЫ","RESTAURANT OVERVIEW"],"Ключевые показатели бронирований, предзаказов и загрузки ресторана.":["Брондау, алдын ала тапсырыс және мейрамхана жүктемесінің негізгі көрсеткіштері.","Key metrics for reservations, preorders and restaurant occupancy."],"Броней сегодня":["Бүгінгі брондаулар","Reservations today"],"все бронирования на сегодня":["бүгінгі барлық брондаулар","all reservations for today"],"Гостей сегодня":["Бүгінгі қонақтар","Guests today"],"по броням на сегодня":["бүгінгі брондаулар бойынша","from today's reservations"],"Активные брони":["Белсенді брондаулар","Active reservations"],"подтверждено + гости пришли":["расталған + келген қонақтар","confirmed + arrived"],"Отменено":["Болдырылмады","Cancelled"],"за всё время":["барлық уақыт бойынша","all time"],"С предзаказом":["Алдын ала тапсырыспен","With preorder"],"броней с блюдами":["тағамдары бар брондаулар","reservations with dishes"],"Сумма предзаказов":["Алдын ала тапсырыстар сомасы","Preorder total"],"по всем предзаказам":["барлық алдын ала тапсырыстар бойынша","all preorders"],"Оплачено депозитов":["Төленген депозиттер","Paid deposits"],"статус «Оплачено»":["«Төленді» мәртебесі","paid status"],"Доступно столов":["Қолжетімді үстелдер","Available tables"],"для новых бронирований":["жаңа брондаулар үшін","for new reservations"],"ОСНОВНЫЕ ГРАФИКИ":["НЕГІЗГІ ГРАФИКТЕР","MAIN CHARTS"],"ДИНАМИКА":["ДИНАМИКА","TRENDS"],"Бронирования за последние 7 дней":["Соңғы 7 күндегі брондаулар","Reservations over the last 7 days"],"СТАТУСЫ":["МӘРТЕБЕЛЕР","STATUSES"],"ЗОНЫ":["АЙМАҚТАР","AREAS"],"Зал и терраса":["Зал және терраса","Hall and terrace"],"ПОПУЛЯРНОСТЬ":["ТАНЫМАЛДЫЛЫҚ","POPULARITY"],"Топ столиков":["Танымал үстелдер","Top tables"],"ВРЕМЯ":["УАҚЫТ","TIME"],"Популярные часы":["Танымал уақыттар","Popular times"],"НИЖНИЕ СПИСКИ":["ТӨМЕНГІ ТІЗІМДЕР","LOWER LISTS"],"БЛИЖАЙШИЕ":["ЖАҚЫНДАҒЫ","UPCOMING"],"Ближайшие бронирования":["Алдағы брондаулар","Upcoming reservations"],"КУХНЯ":["АСҮЙ","KITCHEN"],"Последние предзаказы":["Соңғы алдын ала тапсырыстар","Recent preorders"],"УПРАВЛЕНИЕ РЕСТОРАНОМ":["МЕЙРАМХАНАНЫ БАСҚАРУ","RESTAURANT MANAGEMENT"],"Управление текущими и будущими бронированиями ресторана.":["Мейрамхананың ағымдағы және болашақ брондауларын басқару.","Manage current and future restaurant reservations."],"Сегодня":["Бүгін","Today"],"Подтверждено":["Расталды","Confirmed"],"Гости пришли":["Қонақтар келді","Guests arrived"],"Гость пришёл":["Қонақ келді","Guest arrived"],"Завершено":["Аяқталды","Completed"],"ТЕКУЩИЙ ДЕНЬ":["БҮГІНГІ КҮН","CURRENT DAY"],"Бронирования на сегодня":["Бүгінгі брондаулар","Today's reservations"],"На сегодня бронирований нет.":["Бүгінге брондаулар жоқ.","No reservations for today."],"БАЗА БРОНИРОВАНИЙ":["БРОНДАУЛАР ТІЗІМІ","RESERVATIONS DATABASE"],"Все бронирования":["Барлық брондаулар","All reservations"],"Поиск":["Іздеу","Search"],"Все статусы":["Барлық мәртебелер","All statuses"],"Сбросить":["Тазалау","Reset"],"Клиент":["Клиент","Customer"],"Оплата":["Төлем","Payment"],"Действия":["Әрекеттер","Actions"],"Бронирования не найдены.":["Брондаулар табылмады.","No reservations found."],"Временно отключайте столики, недоступные для новых бронирований.":["Жаңа брондауларға қолжетімсіз үстелдерді уақытша өшіріңіз.","Temporarily disable tables unavailable for new reservations."],"Всего столиков":["Барлық үстелдер","Total tables"],"Доступно":["Қолжетімді","Available"],"Недоступно":["Қолжетімсіз","Unavailable"],"СХЕМА ЗАЛА":["ЗАЛ ЖОСПАРЫ","HALL LAYOUT"],"Управление доступностью":["Қолжетімділікті басқару","Manage availability"],"Не удалось загрузить столики.":["Үстелдерді жүктеу мүмкін болмады.","Could not load tables."],"ОТЧЁТЫ":["ЕСЕПТЕР","REPORTS"],"АНАЛИТИКА":["ТАЛДАУ","ANALYTICS"],"Статистика по бронированиям и загрузке ресторана.":["Брондаулар мен мейрамхана жүктемесінің статистикасы.","Reservation and restaurant occupancy statistics."],"Период":["Кезең","Period"],"За всё время":["Барлық уақыт","All time"],"Последние 7 дней":["Соңғы 7 күн","Last 7 days"],"Последние 30 дней":["Соңғы 30 күн","Last 30 days"],"Последние 90 дней":["Соңғы 90 күн","Last 90 days"],"Всего броней":["Барлық брондаулар","Total reservations"],"за выбранный период":["таңдалған кезең бойынша","for selected period"],"Всего гостей":["Барлық қонақтар","Total guests"],"по всем броням":["барлық брондаулар бойынша","across all reservations"],"успешных посещений":["сәтті келулер","successful visits"],"Процент отмен":["Болдырмау пайызы","Cancellation rate"],"от общего числа":["жалпы санынан","of total"],"Самый востребованный стол":["Ең танымал үстел","Most popular table"],"Нет данных":["Деректер жоқ","No data"],"Популярное время":["Танымал уақыт","Popular time"],"Среднее число гостей":["Орташа қонақ саны","Average guests"],"на одну бронь":["бір брондауға","per reservation"],"Бронирования по датам":["Күндер бойынша брондаулар","Reservations by date"],"Недостаточно данных для графика.":["График үшін деректер жеткіліксіз.","Not enough data for chart."],"Структура бронирований":["Брондаулар құрылымы","Reservation breakdown"],"ЗАГРУЗКА":["ЖҮКТЕМЕ","OCCUPANCY"],"Популярность столов":["Үстелдердің танымалдығы","Table popularity"],"КУХНЯ И ПРЕДЗАКАЗЫ":["АСҮЙ ЖӘНЕ АЛДЫН АЛА ТАПСЫРЫСТАР","KITCHEN AND PREORDERS"],"Только бронирования, в которых гости заранее выбрали блюда.":["Қонақтар алдын ала тағам таңдаған брондаулар ғана.","Only reservations where guests selected dishes in advance."],"Новый":["Жаңа","New"],"Готовится":["Дайындалуда","Preparing"],"Готов":["Дайын","Ready"],"Открыть":["Ашу","Open"],"Подробнее":["Толығырақ","Details"],"Сохранить":["Сақтау","Save"],"Сохранить изменения":["Өзгерістерді сақтау","Save changes"],"Закрыть":["Жабу","Close"],"Изменить":["Өзгерту","Edit"],"Доступен":["Қолжетімді","Available"],"Отключён":["Өшірілген","Disabled"],"Сделать недоступным":["Қолжетімсіз ету","Disable table"],"Сделать доступным":["Қолжетімді ету","Enable table"],"Ближайших броней нет":["Алдағы брондаулар жоқ","No upcoming reservations"],"Предзаказов пока нет":["Әзірге алдын ала тапсырыстар жоқ","No preorders yet"],"Тихая зона":["Тыныш аймақ","Quiet area"],"У окна":["Терезе жанында","By the window"],"Обычный стол":["Кәдімгі үстел","Standard table"],"Детский стул":["Балалар орындығы","High chair"],"День рождения":["Туған күн","Birthday"],"Тихое место":["Тыныш орын","Quiet place"],"Доступный стол":["Қолжетімді үстел","Accessible table"],"Время бронирования":["Брондау уақыты","Reservation time"],"бронирований":["брондау","reservations"],"гост.":["қонақ","guests"],"мест":["орын","seats"],"всего":["барлығы","total"],"броней":["брондау","reservations"],"Стол ресторана":["Мейрамхана үстелі","Restaurant table"],"Основной зал":["Негізгі зал","Main hall"],"ЖУРНАЛ ДЕЙСТВИЙ":["ӘРЕКЕТТЕР ЖУРНАЛЫ","ACTIVITY LOG"],"Редактирование брони":["Брондауды өзгерту","Reservation edited"],"Статус брони":["Брондау мәртебесі","Reservation status"],"Отмена брони":["Брондауды болдырмау","Reservation cancelled"],"Статус предзаказа":["Алдын ала тапсырыс мәртебесі","Preorder status"],"Статус столика":["Үстел мәртебесі","Table status"],"Обновить":["Жаңарту","Refresh"],"Администратор":["Әкімші","Administrator"],"Действие":["Әрекет","Action"],"Изменение":["Өзгеріс","Change"],"Старое значение":["Алдыңғы мән","Previous value"],"Новое значение":["Жаңа мән","New value"],"TABLE — Администратор":["TABLE — Әкімші","TABLE — Administrator"],"TABLE — Бронирование столиков":["TABLE — Үстел брондау","TABLE — Table reservations"],"TABLE — Личный кабинет":["TABLE — Жеке кабинет","TABLE — My account"],"TABLE — Регистрация":["TABLE — Тіркелу","TABLE — Registration"],"TABLE — Вход":["TABLE — Кіру","TABLE — Sign in"],"TABLE — Вход администратора":["TABLE — Әкімшіге кіру","TABLE — Administrator sign in"],"TABLE — Демо-оплата":["TABLE — Демо төлем","TABLE — Demo payment"],"TABLE — Оплата выполнена":["TABLE — Төлем аяқталды","TABLE — Payment complete"],"БРОНИРОВАНИЯ":["БРОНДАУЛАР","RESERVATIONS"],"СТОЛИКИ":["ҮСТЕЛДЕР","TABLES"],"ПРЕДЗАКАЗЫ":["АЛДЫН АЛА ТАПСЫРЫСТАР","PREORDERS"],"Броней с предзаказом":["Алдын ала тапсырысы бар брондаулар","Reservations with preorders"],"Заказано блюд":["Тапсырыс берілген тағамдар","Dishes ordered"],"СПИСОК":["ТІЗІМ","LIST"],"Брони с предзаказом":["Алдын ала тапсырысы бар брондаулар","Reservations with preorders"],"Предзаказов пока нет.":["Әзірге алдын ала тапсырыстар жоқ.","No preorders yet."],"АУДИТ И ИСТОРИЯ":["АУДИТ ЖӘНЕ ТАРИХ","AUDIT AND HISTORY"],"История изменений, выполненных администратором в системе.":["Әкімшінің жүйеде жасаған өзгерістерінің тарихы.","History of changes made by the administrator."],"Всего записей":["Барлық жазбалар","Total entries"],"ИСТОРИЯ ИЗМЕНЕНИЙ":["ӨЗГЕРІСТЕР ТАРИХЫ","CHANGE HISTORY"],"Действия администратора":["Әкімші әрекеттері","Administrator actions"],"Тип действия":["Әрекет түрі","Action type"],"Все действия":["Барлық әрекеттер","All actions"],"Дата и время":["Күні мен уақыты","Date and time"],"Объект":["Нысан","Object"],"Записей журнала пока нет.":["Журналда әзірге жазба жоқ.","No log entries yet."],"ПРЕДЗАКАЗ":["АЛДЫН АЛА ТАПСЫРЫС","PREORDER"],"Бронь №":["Брондау №","Reservation No."],"СТАТУС ПРЕДЗАКАЗА":["АЛДЫН АЛА ТАПСЫРЫС МӘРТЕБЕСІ","PREORDER STATUS"],"Сохранить статус":["Мәртебені сақтау","Save status"],"БЛЮДА":["ТАҒАМДАР","DISHES"],"ПОЖЕЛАНИЯ":["ТІЛЕКТЕР","REQUESTS"],"КОММЕНТАРИЙ":["ТҮСІНІКТЕМЕ","COMMENT"],"ДЕТАЛИ БРОНИ":["БРОНДАУ МӘЛІМЕТТЕРІ","RESERVATION DETAILS"],"Комментарий":["Түсініктеме","Comment"],"Статус бронирования":["Брондау мәртебесі","Reservation status"],"Изменить статус":["Мәртебені өзгерту","Change status"],"Редактировать бронирование":["Брондауды өңдеу","Edit reservation"],"РЕДАКТИРОВАНИЕ БРОНИ":["БРОНДАУДЫ ӨҢДЕУ","EDIT RESERVATION"],"РЕДАКТИРОВАНИЕ":["ӨҢДЕУ","EDITING"],"Имя клиента":["Клиенттің аты","Customer name"],"ВКЛАДКИ":["ҚОЙЫНДЫЛАР","TABS"],"Бронь":["Брондау","Reservation"],"КНОПКИ":["ТҮЙМЕЛЕР","BUTTONS"],"ДАННЫЕ БРОНИ":["БРОНДАУ МӘЛІМЕТТЕРІ","RESERVATION DETAILS"],"ВЕРХ КАРТОЧКИ":["КАРТОЧКАНЫҢ ЖОҒАРҒЫ БӨЛІГІ","CARD HEADER"],"Стол №1 — 2 места":["Үстел №1 — 2 орын","Table No. 1 — 2 seats"],"Стол №2 — 4 места":["Үстел №2 — 4 орын","Table No. 2 — 4 seats"],"Стол №3 — 4 места":["Үстел №3 — 4 орын","Table No. 3 — 4 seats"],"Стол №4 — 6 мест":["Үстел №4 — 6 орын","Table No. 4 — 6 seats"],"Стол №5 — 4 места":["Үстел №5 — 4 орын","Table No. 5 — 4 seats"],"Стол №6 — 4 места":["Үстел №6 — 4 орын","Table No. 6 — 4 seats"],"Стол №7 — 6 мест":["Үстел №7 — 6 орын","Table No. 7 — 6 seats"],"Стол №8 — 2 места":["Үстел №8 — 2 орын","Table No. 8 — 2 seats"],"Стол №9 — 4 места":["Үстел №9 — 4 орын","Table No. 9 — 4 seats"],"Стол №10 — 4 места":["Үстел №10 — 4 орын","Table No. 10 — 4 seats"],"Стол №11 — 2 места":["Үстел №11 — 2 орын","Table No. 11 — 2 seats"],"Стол №12 — 4 места":["Үстел №12 — 4 орын","Table No. 12 — 4 seats"],"Стол №13 — 4 места":["Үстел №13 — 4 орын","Table No. 13 — 4 seats"],"Стол №14 — 4 места":["Үстел №14 — 4 орын","Table No. 14 — 4 seats"],"Стол №15 — 2 места":["Үстел №15 — 2 орын","Table No. 15 — 2 seats"],"Стол №16 — 6 мест":["Үстел №16 — 6 орын","Table No. 16 — 6 seats"]};
  Object.assign(dictionary, {"Предоплата брони": ["Брондаудың алдын ала төлемі", "Booking deposit"], "Выберите способ оплаты": ["Төлем тәсілін таңдаңыз", "Choose payment method"], "Банковская карта": ["Банк картасы", "Bank card"], "Только тестовая карта": ["Тек тест картасы", "Test card only"], "QR-код": ["QR-код", "QR code"], "Демонстрационный QR, не Kaspi-платёж": ["Демо QR, Kaspi төлемі емес", "Demo QR, not a Kaspi payment"], "Демонстрация, без подключения платёжной системы": ["Төлем жүйесіне қосылмаған демо", "Demo without payment integration"], "Номер тестовой карты": ["Тест картасының нөмірі", "Test card number"], "Срок действия": ["Жарамдылық мерзімі", "Expiry date"], "CVC (тестовый)": ["CVC (тест)", "CVC (test)"], "Подтвердить демо-оплату · 5 000 ₸": ["Демо төлемді растау · 5 000 ₸", "Confirm demo payment · 5,000 ₸"], "ЭЛЕКТРОННЫЙ ЧЕК": ["ЭЛЕКТРОНДЫ ТҮБІРТЕК", "ELECTRONIC RECEIPT"], "Бронирование оплачено": ["Брондау төленді", "Reservation paid"], "Чек №": ["Түбіртек №", "Receipt No."], "Демо-оплата подтверждена": ["Демо төлем расталды", "Demo payment confirmed"], "Номер брони": ["Брондау нөмірі", "Reservation number"], "Столик": ["Үстел", "Table"], "Гость": ["Қонақ", "Guest"], "Дата посещения": ["Келу күні", "Visit date"], "Способ": ["Тәсіл", "Method"], "Время оплаты": ["Төлем уақыты", "Payment time"], "Внесённый депозит": ["Төленген депозит", "Deposit paid"], "Распечатать / сохранить PDF": ["Басып шығару / PDF сақтау", "Print / save PDF"], "Тестовая карта": ["Тест картасы", "Test card"], "Демо QR": ["Демо QR", "Demo QR"], "Демо Apple Pay": ["Демо Apple Pay", "Demo Apple Pay"], "Депозит": ["Депозит", "Deposit"], "Стоимость предзаказа:": ["Алдын ала тапсырыс құны:", "Preorder total:"], "Я понимаю, что это демонстрационная оплата": ["Бұл демо төлем екенін түсінемін", "I understand this is a demo payment"], "Подтверждаю демонстрационный платёж": ["Демо төлемді растаймын", "I confirm the demo payment"]});
  const storageTheme = "table-theme";
  const storageLanguage = "table-language";
  const validLanguages = ["ru", "kk", "en"];
  let language = validLanguages.includes(localStorage.getItem(storageLanguage)) ? localStorage.getItem(storageLanguage) : "ru";
  let theme = localStorage.getItem(storageTheme) === "dark" ? "dark" : "light";
  const originals = new WeakMap();
  const lastRendered = new WeakMap();
  const attributeOriginals = new WeakMap();
  const attributeRendered = new WeakMap();
  const translationMap = new Map(Object.entries(dictionary));
  const sortedKeys = [...translationMap.keys()].sort((a,b) => b.length-a.length);
  const patternRules = [
    [/^Стол №\s*(\d+)$/i, ["Үстел №$1", "Table No. $1"]],
    [/^Бронь\s*#(\d+)$/i, ["Брондау #$1", "Reservation #$1"]],
    [/^Стол\s*№\s*(\d+)$/i, ["Үстел №$1", "Table No. $1"]],
    [/^(\d+)\s*бронирований$/i, ["$1 брондау", "$1 reservations"]],
    [/^(\d+)\s*гост\.$/i, ["$1 қонақ", "$1 guests"]],
    [/^(\d+)\s*мест$/i, ["$1 орын", "$1 seats"]],
    [/^СТОЛ\s*№\s*(\d+)$/i, ["ҮСТЕЛ №$1", "TABLE NO. $1"]]
  ];
  function translate(input) {
    if (language === "ru" || !input || !/[А-Яа-яЁё]/.test(input)) return input;
    const index = language === "kk" ? 0 : 1;
    const exact = translationMap.get(input);
    if (exact) return exact[index];
    for (const [re, options] of patternRules) {
      if (re.test(input)) return input.replace(re, options[index]);
    }
    // Translate complete known phrases inside dynamic labels, without touching IDs or values.
    let result = input;
    for (const key of sortedKeys) {
      if (key.length < 7 || !result.includes(key)) continue;
      const translated = translationMap.get(key)[index];
      result = result.split(key).join(translated);
    }
    return result;
  }
  function skipElement(el) {
    return !el || !!el.closest("script,style,textarea,code,pre,[data-i18n-ignore],.table-preferences");
  }
  function updateText(node) {
    if (!node.parentElement || skipElement(node.parentElement)) return;
    const current = node.nodeValue;
    if (!current || !current.trim()) return;
    const old = originals.get(node);
    if (old === undefined || (current !== lastRendered.get(node) && current !== old)) originals.set(node, current);
    const source = originals.get(node);
    const whitespace = source.match(/^(\s*)([\s\S]*?)(\s*)$/);
    if (!whitespace) return;
    const output = whitespace[1] + translate(whitespace[2]) + whitespace[3];
    if (current !== output) node.nodeValue = output;
    lastRendered.set(node, output);
  }
  function updateAttributes(el) {
    if (!(el instanceof Element) || skipElement(el)) return;
    let originalsForElement = attributeOriginals.get(el);
    if (!originalsForElement) { originalsForElement = {}; attributeOriginals.set(el, originalsForElement); }
    let renderedForElement = attributeRendered.get(el);
    if (!renderedForElement) { renderedForElement = {}; attributeRendered.set(el, renderedForElement); }
    for (const attr of ["placeholder", "title", "aria-label"]) {
      if (!el.hasAttribute(attr)) continue;
      const current = el.getAttribute(attr);
      if (originalsForElement[attr] === undefined || (current !== renderedForElement[attr] && current !== originalsForElement[attr])) originalsForElement[attr] = current;
      const value = translate(originalsForElement[attr]);
      if (current !== value) el.setAttribute(attr, value);
      renderedForElement[attr] = value;
    }
  }
  function walk(root) {
    if (!root) return;
    if (root.nodeType === Node.TEXT_NODE) { updateText(root); return; }
    if (root.nodeType !== Node.ELEMENT_NODE && root.nodeType !== Node.DOCUMENT_NODE) return;
    if (root.nodeType === Node.ELEMENT_NODE && skipElement(root)) return;
    if (root.nodeType === Node.ELEMENT_NODE) updateAttributes(root);
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      if (node.nodeType === Node.TEXT_NODE) updateText(node);
      else updateAttributes(node);
    }
  }
  function applyTheme() {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    document.querySelectorAll("[data-theme-choice]").forEach(btn => {
      const selected = btn.dataset.themeChoice === theme;
      btn.setAttribute("aria-pressed", String(selected));
      btn.classList.toggle("is-selected", selected);
    });
  }
  function applyLanguage() {
    document.documentElement.lang = language === "kk" ? "kk" : language;
    document.querySelectorAll("[data-language-choice]").forEach(btn => {
      const selected = btn.dataset.languageChoice === language;
      btn.setAttribute("aria-pressed", String(selected));
      btn.classList.toggle("is-selected", selected);
    });
    walk(document.body);
    if (document.title) {
      const title = document.title;
      if (!window.__originalTitle || (title !== window.__renderedTitle && title !== window.__originalTitle)) window.__originalTitle = title;
      document.title = translate(window.__originalTitle);
      window.__renderedTitle = document.title;
    }
  }
  function createControls() {
    const aside = document.createElement("aside");
    aside.className = "table-preferences";
    aside.setAttribute("aria-label", "Theme and language settings");
    aside.innerHTML = `<div class="table-preferences-themes" role="group" aria-label="Theme">
      <button type="button" data-theme-choice="light" title="Light theme" aria-label="Light theme">☀</button>
      <button type="button" data-theme-choice="dark" title="Dark theme" aria-label="Dark theme">☾</button>
      </div><span class="table-preferences-divider"></span>
      <div class="table-preferences-languages" role="group" aria-label="Language">
      <button type="button" data-language-choice="ru">RU</button>
      <button type="button" data-language-choice="kk">ҚАЗ</button>
      <button type="button" data-language-choice="en">EN</button></div>`;
    aside.addEventListener("click", e => {
      const themeButton = e.target.closest("[data-theme-choice]");
      const languageButton = e.target.closest("[data-language-choice]");
      if (themeButton) { theme = themeButton.dataset.themeChoice; localStorage.setItem(storageTheme, theme); applyTheme(); }
      if (languageButton) { language = languageButton.dataset.languageChoice; localStorage.setItem(storageLanguage, language); applyLanguage(); }
    });
    document.body.appendChild(aside);
    applyTheme();
    applyLanguage();
  }
  let queued = false;
  const observer = new MutationObserver(records => {
    if (queued) return;
    if (!records.some(record => record.type === "childList" || record.type === "characterData")) return;
    queued = true;
    queueMicrotask(() => { queued = false; walk(document.body); });
  });
  function start() {
    createControls();
    observer.observe(document.body, {subtree:true,childList:true,characterData:true});
  }
  document.documentElement.dataset.theme = theme;
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start, {once:true});
  else start();
})();