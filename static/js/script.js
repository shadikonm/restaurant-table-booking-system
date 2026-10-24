const date = document.getElementById("date");
const time = document.getElementById("time");
const guests = document.getElementById("guests");

const showTablesButton = document.getElementById("showTablesButton");
const pageMessage = document.getElementById("pageMessage");

const tables = [
    ...document.querySelectorAll(".table")
];

const bookingModal = document.getElementById("bookingModal");
const closeModal = document.getElementById("closeModal");
const bookingForm = document.getElementById("bookingForm");
const bookingError = document.getElementById("bookingError");

const confirmBookingButton =
    document.getElementById("confirmBookingButton");

const successModal = document.getElementById("successModal");
const successClose = document.getElementById("successClose");


/* =========================================================
   ПРЕДЗАКАЗ БЛЮД
========================================================= */

let restaurantMenu = [];

const preorder = new Map();

let activeMenuCategory = "Все";

const menuItemsContainer =
    document.getElementById("menuItems");

const menuCategoriesContainer =
    document.getElementById("menuCategories");

const menuLoading =
    document.getElementById("menuLoading");

const preorderTotalElement =
    document.getElementById("preorderTotal");


function money(value) {

    return `${Number(value || 0).toLocaleString("ru-RU")} ₸`;
}


function getPreorderPayload() {

    return [...preorder.entries()]
        .filter(([, quantity]) => quantity > 0)
        .map(([menuItemId, quantity]) => ({
            menu_item_id: Number(menuItemId),
            quantity: Number(quantity)
        }));
}


function getPreorderTotal() {

    return restaurantMenu.reduce(
        (total, item) => {

            const quantity =
                preorder.get(
                    Number(item.id)
                ) || 0;

            return (
                total +
                Number(item.price) *
                quantity
            );
        },
        0
    );
}


function updatePreorderTotal() {

    if (!preorderTotalElement) {
        return;
    }

    preorderTotalElement.textContent =
        money(
            getPreorderTotal()
        );
}


function renderMenuCategories() {

    if (!menuCategoriesContainer) {
        return;
    }

    const categories = [
        "Все",
        ...new Set(
            restaurantMenu.map(
                (item) => item.category
            )
        )
    ];

    menuCategoriesContainer.innerHTML =
        categories
            .map(
                (category) => `
                    <button
                        type="button"
                        class="menu-category-button ${
                            category === activeMenuCategory
                                ? "active"
                                : ""
                        }"
                        data-menu-category="${category}"
                    >
                        ${category}
                    </button>
                `
            )
            .join("");
}


function renderMenuItems() {

    if (!menuItemsContainer) {
        return;
    }

    const items =
        activeMenuCategory === "Все"
            ? restaurantMenu
            : restaurantMenu.filter(
                (item) =>
                    item.category ===
                    activeMenuCategory
            );


    if (!items.length) {

        menuItemsContainer.innerHTML =
            `
                <p class="menu-empty">
                    В этой категории пока нет блюд.
                </p>
            `;

        return;
    }


    menuItemsContainer.innerHTML =
        items
            .map(
                (item) => {

                    const quantity =
                        preorder.get(
                            Number(item.id)
                        ) || 0;

                    return `
                        <article class="menu-item-card">

                            <div class="menu-item-content">

                                <span class="menu-item-category">
                                    ${item.category}
                                </span>

                                <h4>
                                    ${item.name}
                                </h4>

                                <p>
                                    ${item.description || ""}
                                </p>

                            </div>


                            <div class="menu-item-footer">

                                <strong>
                                    ${money(item.price)}
                                </strong>


                                <div class="menu-quantity">

                                    <button
                                        type="button"
                                        data-menu-action="minus"
                                        data-menu-id="${item.id}"
                                        aria-label="Уменьшить количество"
                                    >
                                        −
                                    </button>


                                    <span>
                                        ${quantity}
                                    </span>


                                    <button
                                        type="button"
                                        data-menu-action="plus"
                                        data-menu-id="${item.id}"
                                        aria-label="Увеличить количество"
                                    >
                                        +
                                    </button>

                                </div>

                            </div>

                        </article>
                    `;
                }
            )
            .join("");
}


function resetPreorder() {

    preorder.clear();

    activeMenuCategory =
        "Все";

    renderMenuCategories();

    renderMenuItems();

    updatePreorderTotal();
}


async function loadMenu() {

    if (!menuItemsContainer) {
        return;
    }


    try {

        const response =
            await fetch(
                "/api/menu"
            );


        const result =
            await response.json();


        if (
            !response.ok ||
            !result.success
        ) {

            throw new Error(
                result.message ||
                "Не удалось загрузить меню."
            );
        }


        restaurantMenu =
            result.menu || [];


        if (menuLoading) {

            menuLoading.hidden =
                true;
        }


        renderMenuCategories();

        renderMenuItems();

        updatePreorderTotal();


    } catch (error) {

        console.error(error);


        if (menuLoading) {

            menuLoading.textContent =
                "Не удалось загрузить меню. Бронь можно создать без предзаказа.";
        }
    }
}


if (menuCategoriesContainer) {

    menuCategoriesContainer.addEventListener(
        "click",
        (event) => {

            const button =
                event.target.closest(
                    "[data-menu-category]"
                );


            if (!button) {
                return;
            }


            activeMenuCategory =
                button.dataset.menuCategory;


            renderMenuCategories();

            renderMenuItems();
        }
    );
}


if (menuItemsContainer) {

    menuItemsContainer.addEventListener(
        "click",
        (event) => {

            const button =
                event.target.closest(
                    "[data-menu-action]"
                );


            if (!button) {
                return;
            }


            const id =
                Number(
                    button.dataset.menuId
                );


            const current =
                preorder.get(id) || 0;


            if (
                button.dataset.menuAction ===
                "plus"
            ) {

                preorder.set(
                    id,
                    Math.min(
                        current + 1,
                        20
                    )
                );

            } else {

                const next =
                    Math.max(
                        current - 1,
                        0
                    );


                if (next === 0) {

                    preorder.delete(id);

                } else {

                    preorder.set(
                        id,
                        next
                    );
                }
            }


            renderMenuItems();

            updatePreorderTotal();
        }
    );
}


loadMenu();


/* =========================================================
   ДАТА
========================================================= */

function localDate() {

    const now =
        new Date();


    const year =
        now.getFullYear();


    const month =
        String(
            now.getMonth() + 1
        ).padStart(
            2,
            "0"
        );


    const day =
        String(
            now.getDate()
        ).padStart(
            2,
            "0"
        );


    return `${year}-${month}-${day}`;
}


function prettyDate(value) {

    if (!value) {

        return "—";
    }


    const parts =
        value.split("-");


    if (
        parts.length !== 3
    ) {

        return value;
    }


    return `${parts[2]}.${parts[1]}.${parts[0]}`;
}


date.min =
    localDate();

date.value =
    localDate();


/* =========================================================
   ЗАЛ / ТЕРРАСА
========================================================= */

const hallTab =
    document.getElementById(
        "hallTab"
    );

const terraceTab =
    document.getElementById(
        "terraceTab"
    );

const hallMap =
    document.getElementById(
        "hallMap"
    );

const terraceMap =
    document.getElementById(
        "terraceMap"
    );


function showHall() {

    hallTab.classList.add(
        "active"
    );

    terraceTab.classList.remove(
        "active"
    );


    hallMap.classList.add(
        "active-map"
    );

    terraceMap.classList.remove(
        "active-map"
    );
}


function showTerrace() {

    terraceTab.classList.add(
        "active"
    );

    hallTab.classList.remove(
        "active"
    );


    terraceMap.classList.add(
        "active-map"
    );

    hallMap.classList.remove(
        "active-map"
    );
}


hallTab.addEventListener(
    "click",
    showHall
);


terraceTab.addEventListener(
    "click",
    showTerrace
);


/* =========================================================
   СОСТОЯНИЕ СТОЛОВ
========================================================= */

function resetTables() {

    tables.forEach(
        (table) => {

            table.classList.remove(
                "free",
                "busy",
                "unsuitable"
            );


            table.classList.add(
                "unavailable"
            );


            table.disabled =
                true;
        }
    );
}


function setTableState(
    table,
    state
) {

    table.classList.remove(
        "free",
        "busy",
        "unsuitable",
        "unavailable"
    );


    table.classList.add(
        state
    );


    table.disabled =
        state !== "free";
}


resetTables();


/* =========================================================
   ИЗМЕНЕНИЕ ПАРАМЕТРОВ
========================================================= */

[
    date,
    time,
    guests
].forEach(
    (element) => {

        element.addEventListener(
            "change",
            () => {

                resetTables();


                pageMessage.classList.remove(
                    "ok"
                );


                pageMessage.textContent =
                    "Нажмите «Показать столы», чтобы обновить доступность.";
            }
        );
    }
);


/* =========================================================
   ПРОВЕРКА ДОСТУПНОСТИ
========================================================= */

async function checkAvailability() {

    pageMessage.textContent = "";
    pageMessage.classList.remove("ok");

    if (!date.value || !time.value || !guests.value) {
        pageMessage.textContent =
            "Выберите дату, время и количество гостей.";
        return;
    }

    showTablesButton.disabled = true;
    showTablesButton.textContent = "Проверяем...";

    try {

        const params = new URLSearchParams({
            date: date.value,
            time: time.value,
            guests: guests.value
        });

        const response = await fetch(
            `/api/availability?${params.toString()}`
        );

        const result = await response.json();

        if (!response.ok || !result.success) {

            resetTables();

            pageMessage.textContent =
                result.message ||
                "Не удалось проверить доступность.";

            return;
        }

        const busyTables = new Set(
            (result.busy_tables || []).map(Number)
        );

        const unsuitableTables = new Set(
            (result.unsuitable_tables || []).map(Number)
        );

        const disabledTables = new Set(
            (result.disabled_tables || []).map(Number)
        );

        let freeCount = 0;

        tables.forEach((table) => {

            const tableNumber =
                Number(table.dataset.table);

            if (disabledTables.has(tableNumber)) {

                setTableState(
                    table,
                    "unavailable"
                );

                return;
            }

            if (unsuitableTables.has(tableNumber)) {

                setTableState(
                    table,
                    "unsuitable"
                );

                return;
            }

            if (busyTables.has(tableNumber)) {

                setTableState(
                    table,
                    "busy"
                );

                return;
            }

            setTableState(
                table,
                "free"
            );

            freeCount += 1;
        });

        if (freeCount === 0) {

            pageMessage.classList.remove("ok");

            pageMessage.textContent =
                "На выбранное время свободных подходящих столов нет.";

        } else {

            pageMessage.classList.add("ok");

            pageMessage.textContent =
                `Свободных подходящих столов: ${freeCount}. Выберите стол.`;
        }

    } catch (error) {

        console.error(error);

        resetTables();

        pageMessage.textContent =
            "Не удалось связаться с сервером.";

    } finally {

        showTablesButton.disabled = false;

        showTablesButton.textContent =
            "Показать столы";
    }
}

showTablesButton.addEventListener(
    "click",
    checkAvailability
);


/* =========================================================
   ОСОБЫЕ ПОЖЕЛАНИЯ
========================================================= */

const specialRequestInputs = [
    ...document.querySelectorAll(
        'input[name="specialRequest"]'
    )
];


const reservationComment =
    document.getElementById(
        "reservationComment"
    );


function getSelectedSpecialRequests() {

    return specialRequestInputs
        .filter(
            (input) =>
                input.checked &&
                !input.disabled
        )
        .map(
            (input) =>
                input.value
        );
}


function resetSpecialRequests() {

    specialRequestInputs.forEach(
        (input) => {

            input.checked =
                false;

            input.disabled =
                false;


            const label =
                input.closest(
                    ".special-option"
                );


            if (label) {

                label.classList.remove(
                    "disabled-option"
                );
            }
        }
    );


    if (reservationComment) {

        reservationComment.value =
            "";
    }
}


function configureSpecialRequests(
    table
) {

    const tableNumber =
        Number(
            table.dataset.table
        );


    const allowedByTable = {

        window:
            [1, 2, 3, 4],

        quiet:
            [4, 7, 10, 11, 13, 15],

        accessible:
            [7, 14, 16]
    };


    specialRequestInputs.forEach(
        (input) => {

            input.disabled =
                false;


            const label =
                input.closest(
                    ".special-option"
                );


            if (label) {

                label.classList.remove(
                    "disabled-option"
                );
            }


            const allowedTables =
                allowedByTable[
                    input.value
                ];


            if (
                allowedTables &&
                !allowedTables.includes(
                    tableNumber
                )
            ) {

                input.checked =
                    false;

                input.disabled =
                    true;


                if (label) {

                    label.classList.add(
                        "disabled-option"
                    );
                }
            }
        }
    );
}


/* =========================================================
   ОТКРЫТИЕ БРОНИ
========================================================= */

tables.forEach(
    (table) => {

        table.addEventListener(
            "click",
            () => {

                if (
                    !table.classList.contains(
                        "free"
                    )
                ) {

                    return;
                }


                const tableNumber =
                    table.dataset.table;


                const zone =
                    table.dataset.zone ||
                    "—";


                const features =
                    table.dataset.features ||
                    "Стандартный стол";


                document.getElementById(
                    "selectedTable"
                ).textContent =
                    tableNumber;


                document.getElementById(
                    "tableNumber"
                ).value =
                    tableNumber;


                document.getElementById(
                    "selectedTableZone"
                ).textContent =
                    zone;


                document.getElementById(
                    "selectedTableFeatures"
                ).textContent =
                    features;


                document.getElementById(
                    "summaryDate"
                ).textContent =
                    prettyDate(
                        date.value
                    );


                document.getElementById(
                    "summaryTime"
                ).textContent =
                    time.value;


                document.getElementById(
                    "summaryGuests"
                ).textContent =
                    guests.value;


                bookingError.textContent =
                    "";


                resetSpecialRequests();

                configureSpecialRequests(
                    table
                );


                bookingModal.classList.add(
                    "active"
                );
            }
        );
    }
);


/* =========================================================
   ЗАКРЫТИЕ ОКНА БРОНИ
========================================================= */

function closeBookingModal() {

    bookingModal.classList.remove(
        "active"
    );


    bookingError.textContent =
        "";
}


closeModal.addEventListener(
    "click",
    closeBookingModal
);


bookingModal.addEventListener(
    "click",
    (event) => {

        if (
            event.target ===
            bookingModal
        ) {

            closeBookingModal();
        }
    }
);


/* =========================================================
   СОЗДАНИЕ БРОНИ
========================================================= */

bookingForm.addEventListener(
    "submit",
    async (event) => {

        event.preventDefault();


        bookingError.textContent =
            "";


        const tableNumber =
            document.getElementById(
                "tableNumber"
            ).value;


        const customerName =
            document.getElementById(
                "customerName"
            ).value.trim();


        const phone =
            document.getElementById(
                "phone"
            ).value.trim();


        if (
            !tableNumber ||
            !customerName ||
            !phone
        ) {

            bookingError.textContent =
                "Заполните имя и телефон.";

            return;
        }


        const payload = {

            table_number:
                Number(
                    tableNumber
                ),

            customer_name:
                customerName,

            phone:
                phone,

            guests:
                Number(
                    guests.value
                ),

            reservation_date:
                date.value,

            reservation_time:
                time.value,

            special_requests:
                getSelectedSpecialRequests(),

            comment:
                reservationComment
                    ? reservationComment.value.trim()
                    : "",

            preorder:
                getPreorderPayload()
        };


        confirmBookingButton.disabled =
            true;


        confirmBookingButton.textContent =
            "Создаём бронь...";


        try {

            const response =
                await fetch(
                    "/api/reservations",
                    {
                        method:
                            "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify(
                                payload
                            )
                    }
                );


            const result =
                await response.json();


            if (
                !response.ok ||
                !result.success
            ) {

                bookingError.textContent =
                    result.message ||
                    "Не удалось создать бронирование.";

                return;
            }


            document.getElementById(
                "successId"
            ).textContent =
                result.reservation_id;


            document.getElementById(
                "successTable"
            ).textContent =
                `№${tableNumber}`;


            document.getElementById(
                "successDate"
            ).textContent =
                prettyDate(
                    date.value
                );


            document.getElementById(
                "successTime"
            ).textContent =
                time.value;


            const successPreorderBlock =
                document.getElementById(
                    "successPreorderBlock"
                );


            const successPreorderTotal =
                document.getElementById(
                    "successPreorderTotal"
                );


            if (
                result.preorder_total > 0
            ) {

                successPreorderBlock.hidden =
                    false;


                successPreorderTotal.textContent =
                    money(
                        result.preorder_total
                    );

            } else {

                successPreorderBlock.hidden =
                    true;
            }


            bookingForm.reset();


            resetSpecialRequests();

            resetPreorder();


            bookingModal.classList.remove(
                "active"
            );


            successModal.classList.add(
                "active"
            );


            await checkAvailability();


        } catch (error) {

            console.error(error);


            bookingError.textContent =
                "Не удалось связаться с сервером.";

        } finally {

            confirmBookingButton.disabled =
                false;


            confirmBookingButton.textContent =
                "Подтвердить бронирование";
        }
    }
);


/* =========================================================
   УСПЕШНАЯ БРОНЬ
========================================================= */

function closeSuccessModal() {

    successModal.classList.remove(
        "active"
    );
}


successClose.addEventListener(
    "click",
    closeSuccessModal
);


successModal.addEventListener(
    "click",
    (event) => {

        if (
            event.target ===
            successModal
        ) {

            closeSuccessModal();
        }
    }
);


/* =========================================================
   МОЯ БРОНЬ
========================================================= */

const openMyReservation =
    document.getElementById(
        "openMyReservation"
    );


const myReservationModal =
    document.getElementById(
        "myReservationModal"
    );


const closeMyReservation =
    document.getElementById(
        "closeMyReservation"
    );


const myReservationForm =
    document.getElementById(
        "myReservationForm"
    );


const myReservationError =
    document.getElementById(
        "myReservationError"
    );


const myReservationCardModal =
    document.getElementById(
        "myReservationCardModal"
    );


const closeMyReservationCard =
    document.getElementById(
        "closeMyReservationCard"
    );


const cancelMyReservationButton =
    document.getElementById(
        "cancelMyReservationButton"
    );


const backToSearchButton =
    document.getElementById(
        "backToSearchButton"
    );


let currentReservation =
    null;


let currentReservationPhone =
    "";


const statusNames = {

    confirmed:
        "Подтверждено",

    arrived:
        "Гость пришёл",

    completed:
        "Завершено",

    cancelled:
        "Отменено"
};


/* =========================================================
   ОТКРЫТЬ МОЮ БРОНЬ
========================================================= */

openMyReservation.addEventListener(
    "click",
    () => {

        myReservationError.textContent =
            "";


        myReservationModal.classList.add(
            "active"
        );
    }
);


/* =========================================================
   ЗАКРЫТЬ МОЮ БРОНЬ
========================================================= */

closeMyReservation.addEventListener(
    "click",
    () => {

        myReservationModal.classList.remove(
            "active"
        );
    }
);


closeMyReservationCard.addEventListener(
    "click",
    () => {

        myReservationCardModal.classList.remove(
            "active"
        );
    }
);


/* =========================================================
   ПОКАЗАТЬ КАРТОЧКУ БРОНИ
========================================================= */

function showReservationCard(
    reservation
) {

    currentReservation =
        reservation;


    document.getElementById(
        "myCardId"
    ).textContent =
        reservation.id;


    document.getElementById(
        "myCardName"
    ).textContent =
        reservation.customer_name;


    document.getElementById(
        "myCardPhone"
    ).textContent =
        reservation.phone;


    document.getElementById(
        "myCardTable"
    ).textContent =
        `Стол №${reservation.table_number}`;


    document.getElementById(
        "myCardGuests"
    ).textContent =
        reservation.guests;


    document.getElementById(
        "myCardDate"
    ).textContent =
        prettyDate(
            reservation.reservation_date
        );


    document.getElementById(
        "myCardTime"
    ).textContent =
        reservation.reservation_time;


    /* ПРЕДЗАКАЗ */

    const myCardPreorder =
        document.getElementById(
            "myCardPreorder"
        );


    const myCardPreorderItems =
        document.getElementById(
            "myCardPreorderItems"
        );


    const myCardPreorderTotal =
        document.getElementById(
            "myCardPreorderTotal"
        );


    const preorderItems =
        reservation.preorder_items ||
        [];


    if (
        preorderItems.length > 0
    ) {

        myCardPreorder.hidden =
            false;


        myCardPreorderItems.innerHTML =
            preorderItems
                .map(
                    (item) => `
                        <div>
                            <span>
                                ${item.name} × ${item.quantity}
                            </span>

                            <strong>
                                ${money(item.total)}
                            </strong>
                        </div>
                    `
                )
                .join("");


        myCardPreorderTotal.textContent =
            money(
                reservation.preorder_total
            );

    } else {

        myCardPreorder.hidden =
            true;


        myCardPreorderItems.innerHTML =
            "";


        myCardPreorderTotal.textContent =
            money(0);
    }


    /* СТАТУС */

    const status =
        document.getElementById(
            "myCardStatus"
        );


    status.textContent =
        statusNames[
            reservation.status
        ] ||
        reservation.status;


    status.className =
        `my-status ${reservation.status}`;


    const message =
        document.getElementById(
            "myCardMessage"
        );


    message.textContent =
        "";


    message.classList.remove(
        "my-success-message"
    );


    if (
        reservation.status ===
        "confirmed"
    ) {

        cancelMyReservationButton.disabled =
            false;


        cancelMyReservationButton.textContent =
            "Отменить бронирование";

    } else {

        cancelMyReservationButton.disabled =
            true;


        if (
            reservation.status ===
            "cancelled"
        ) {

            cancelMyReservationButton.textContent =
                "Бронирование отменено";

        } else if (
            reservation.status ===
            "arrived"
        ) {

            cancelMyReservationButton.textContent =
                "Гость уже прибыл";

        } else {

            cancelMyReservationButton.textContent =
                "Бронирование завершено";
        }
    }


    myReservationModal.classList.remove(
        "active"
    );


    myReservationCardModal.classList.add(
        "active"
    );
}


/* =========================================================
   ПОИСК БРОНИ
========================================================= */

myReservationForm.addEventListener(
    "submit",
    async (event) => {

        event.preventDefault();


        const reservationId =
            document.getElementById(
                "myReservationId"
            ).value;


        const phone =
            document.getElementById(
                "myReservationPhone"
            ).value.trim();


        myReservationError.textContent =
            "";


        if (
            !reservationId ||
            !phone
        ) {

            myReservationError.textContent =
                "Введите номер брони и телефон.";

            return;
        }


        try {

            const response =
                await fetch(
                    "/api/my-reservation",
                    {
                        method:
                            "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify({
                                reservation_id:
                                    reservationId,

                                phone:
                                    phone
                            })
                    }
                );


            const result =
                await response.json();


            if (
                !response.ok ||
                !result.success
            ) {

                myReservationError.textContent =
                    result.message ||
                    "Бронирование не найдено.";

                return;
            }


            currentReservationPhone =
                phone;


            showReservationCard(
                result.reservation
            );


        } catch (error) {

            console.error(error);


            myReservationError.textContent =
                "Не удалось связаться с сервером.";
        }
    }
);


/* =========================================================
   ОТМЕНА БРОНИ
========================================================= */

cancelMyReservationButton.addEventListener(
    "click",
    async () => {

        if (
            !currentReservation ||
            currentReservation.status !==
                "confirmed"
        ) {

            return;
        }


        const confirmed =
            window.confirm(
                "Вы действительно хотите отменить бронирование?"
            );


        if (!confirmed) {

            return;
        }


        const message =
            document.getElementById(
                "myCardMessage"
            );


        message.textContent =
            "";


        try {

            const response =
                await fetch(
                    `/api/my-reservation/${currentReservation.id}/cancel`,
                    {
                        method:
                            "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify({
                                phone:
                                    currentReservationPhone
                            })
                    }
                );


            const result =
                await response.json();


            if (
                !response.ok ||
                !result.success
            ) {

                message.textContent =
                    result.message ||
                    "Не удалось отменить бронирование.";

                return;
            }


            currentReservation.status =
                "cancelled";


            const status =
                document.getElementById(
                    "myCardStatus"
                );


            status.textContent =
                "Отменено";


            status.className =
                "my-status cancelled";


            cancelMyReservationButton.disabled =
                true;


            cancelMyReservationButton.textContent =
                "Бронирование отменено";


            message.textContent =
                "Бронирование успешно отменено.";


            message.classList.add(
                "my-success-message"
            );


            await checkAvailability();


        } catch (error) {

            console.error(error);


            message.textContent =
                "Не удалось связаться с сервером.";
        }
    }
);


/* =========================================================
   НАЗАД К ПОИСКУ
========================================================= */

backToSearchButton.addEventListener(
    "click",
    () => {

        myReservationCardModal.classList.remove(
            "active"
        );


        myReservationError.textContent =
            "";


        myReservationModal.classList.add(
            "active"
        );
    }
);


/* =========================================================
   КЛИК ПО ФОНУ МОДАЛЬНЫХ ОКОН
========================================================= */

myReservationModal.addEventListener(
    "click",
    (event) => {

        if (
            event.target ===
            myReservationModal
        ) {

            myReservationModal.classList.remove(
                "active"
            );
        }
    }
);


myReservationCardModal.addEventListener(
    "click",
    (event) => {

        if (
            event.target ===
            myReservationCardModal
        ) {

            myReservationCardModal.classList.remove(
                "active"
            );
        }
    }
);


/* =========================================================
   ESC — ЗАКРЫТИЕ ОКОН
========================================================= */

document.addEventListener(
    "keydown",
    (event) => {

        if (
            event.key !==
            "Escape"
        ) {

            return;
        }


        bookingModal.classList.remove(
            "active"
        );


        successModal.classList.remove(
            "active"
        );


        myReservationModal.classList.remove(
            "active"
        );


        myReservationCardModal.classList.remove(
            "active"
        );
    }
);