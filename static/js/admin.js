
const $ = (id) => document.getElementById(id);

let reservations = [];
let restaurantTables = [];
let selectedReservationId = null;
let adminLogs = [];


// =========================================================
// ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
// =========================================================

function statusText(status) {
    const statuses = {
        confirmed: "Подтверждено",
        arrived: "Гость пришёл",
        completed: "Завершено",
        cancelled: "Отменено"
    };

    return statuses[status] || status;
}


function paymentText(status) {
    const statuses = {
        unpaid: "Не оплачено",
        paid: "Оплачено",
        refunded: "Возврат"
    };

    return statuses[status] || status || "Не оплачено";
}


function paymentMethodText(method) {
    const methods = {
        card: "Банковская карта",
        kaspi: "Kaspi",
        apple_pay: "Apple Pay"
    };

    return methods[method] || "—";
}


function specialRequestsText(value) {
    if (!value) {
        return "—";
    }

    const labels = {
        window: "🪟 Столик у окна",
        child_chair: "👶 Детский стул",
        birthday: "🎂 День рождения",
        quiet: "🔇 Тихое место",
        accessible: "♿ Доступный стол"
    };

    let items = [];

    if (Array.isArray(value)) {
        items = value;
    } else {
        items = String(value)
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean);
    }

    if (items.length === 0) {
        return "—";
    }

    return items
        .map((item) => labels[item] || item)
        .join(", ");
}


function formatDate(dateString) {
    if (!dateString) {
        return "—";
    }

    const date = new Date(`${dateString}T00:00:00`);

    return date.toLocaleDateString("ru-RU");
}


function getTodayString() {
    const now = new Date();

    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");

    return `${year}-${month}-${day}`;
}


// =========================================================
// НАВИГАЦИЯ
// =========================================================

document.querySelectorAll(".nav-tab").forEach((button) => {
    button.addEventListener("click", () => {

        document.querySelectorAll(".nav-tab").forEach((tab) => {
            tab.classList.remove("active");
        });

        document.querySelectorAll(".admin-page-section").forEach((section) => {
            section.classList.remove("active");
        });

        button.classList.add("active");

        const sectionId = button.dataset.section;
        const section = $(sectionId);

        if (section) {
            section.classList.add("active");
        }

        if (sectionId === "dashboardSection") {
            renderDashboard();
        }

        if (sectionId === "reportsSection") {
            renderReports();
        }

        if (sectionId === "tablesSection") {
            loadTables();
        }

        if (sectionId === "preordersSection") {
            renderPreorders();
        }

        if (sectionId === "logsSection") {
            loadAdminLogs();
        }
    });
});


// =========================================================
// ЗАГРУЗКА БРОНИРОВАНИЙ
// =========================================================

async function loadReservations() {
    try {
        const response = await fetch("/api/reservations");

        if (response.status === 401) {
            window.location.href = "/admin/login";
            return;
        }

        const data = await response.json();

        if (!response.ok || !data.success) {
            console.error(
                data.message || "Не удалось загрузить бронирования."
            );
            return;
        }

        reservations = data.reservations || [];

        renderStatistics();
        renderTodayReservations();
        renderReservations();
        renderPreorders();
        renderDashboard();

    } catch (error) {
        console.error(
            "Ошибка загрузки бронирований:",
            error
        );
    }
}


// =========================================================
// СТАТИСТИКА
// =========================================================

function renderStatistics() {
    const today = getTodayString();

    const todayReservations = reservations.filter(
        (reservation) =>
            reservation.reservation_date === today
    );

    $("todayCount").textContent =
        todayReservations.length;

    $("confirmedCount").textContent =
        reservations.filter(
            (reservation) =>
                reservation.status === "confirmed"
        ).length;

    $("arrivedCount").textContent =
        reservations.filter(
            (reservation) =>
                reservation.status === "arrived"
        ).length;

    $("completedCount").textContent =
        reservations.filter(
            (reservation) =>
                reservation.status === "completed"
        ).length;

    $("cancelledCount").textContent =
        reservations.filter(
            (reservation) =>
                reservation.status === "cancelled"
        ).length;

    const todayDate = new Date();

    $("todayDate").textContent =
        todayDate.toLocaleDateString(
            "ru-RU",
            {
                day: "numeric",
                month: "long",
                year: "numeric"
            }
        );
}


// =========================================================
// БРОНИРОВАНИЯ НА СЕГОДНЯ
// =========================================================

function renderTodayReservations() {
    const container = $("todayReservations");
    const empty = $("todayEmpty");

    container.innerHTML = "";

    const today = getTodayString();

    const items = reservations
        .filter(
            (reservation) =>
                reservation.reservation_date === today
        )
        .sort(

            (a, b) =>
                a.reservation_time.localeCompare(
                    b.reservation_time
                )
        );

    if (items.length === 0) {
        empty.style.display = "block";
        return;
    }

    empty.style.display = "none";

    items.forEach((reservation) => {
        const card = document.createElement("div");

        card.className = "today-card";

        card.innerHTML = `
            <div class="today-time">
                ${reservation.reservation_time}
            </div>

            <div class="today-table">
                Стол №${reservation.table_number}
            </div>

            <div class="today-client">
                <strong>${reservation.customer_name}</strong>
                <span>${reservation.phone}</span>
            </div>

            <div class="today-guests">
                ${reservation.guests} гост.
            </div>

            <div>
                <span class="status status-${reservation.status}">
                    ${statusText(reservation.status)}
                </span>
            </div>

            <div>
                <button
                    type="button"
                    class="view-button"
                    data-reservation-id="${reservation.id}"
                >
                    Открыть
                </button>
            </div>
        `;

        container.appendChild(card);
    });
}


// =========================================================
// ФИЛЬТРЫ
// =========================================================

function getFilteredReservations() {
    const search =
        $("searchInput").value
            .trim()
            .toLowerCase();

    const date =
        $("dateFilter").value;

    const status =
        $("statusFilter").value;

    return reservations.filter((reservation) => {

        const searchText = `
            ${reservation.id}
            ${reservation.customer_name}
            ${reservation.phone}
        `.toLowerCase();

        const matchesSearch =
            !search ||
            searchText.includes(search);

        const matchesDate =
            !date ||
            reservation.reservation_date === date;

        const matchesStatus =
            status === "all" ||
            reservation.status === status;

        return (
            matchesSearch &&
            matchesDate &&
            matchesStatus
        );
    });
}


// =========================================================
// ТАБЛИЦА ВСЕХ БРОНИРОВАНИЙ
// =========================================================

function renderReservations() {
    const tbody = $("reservationsTable");
    const empty = $("emptyState");

    tbody.innerHTML = "";

    const filtered = getFilteredReservations();

    if (filtered.length === 0) {
        empty.style.display = "block";
        return;
    }

    empty.style.display = "none";

    filtered.forEach((reservation) => {
        const row = document.createElement("tr");

        const paymentStatus =
            reservation.payment_status || "unpaid";

        row.innerHTML = `
            <td>#${reservation.id}</td>

            <td class="client-name">
                ${reservation.customer_name}
            </td>

            <td>${reservation.phone}</td>

            <td>№${reservation.table_number}</td>

            <td>${reservation.guests}</td>

            <td>
                ${formatDate(reservation.reservation_date)}
            </td>

            <td>
                ${reservation.reservation_time}
            </td>

            <td>
                <span class="status status-${reservation.status}">
                    ${statusText(reservation.status)}
                </span>
            </td>

            <td>
                <span class="payment-admin ${paymentStatus}">
                    ${paymentText(paymentStatus)}
                </span>
            </td>

            <td>
                <button
                    type="button"
                    class="view-button"
                    data-reservation-id="${reservation.id}"
                >
                    Открыть
                </button>
            </td>
        `;

        tbody.appendChild(row);
    });
}


$("searchInput").addEventListener(
    "input",
    renderReservations
);

$("dateFilter").addEventListener(
    "change",
    renderReservations
);

$("statusFilter").addEventListener(
    "change",
    renderReservations
);

$("resetFilters").addEventListener(
    "click",
    () => {
        $("searchInput").value = "";
        $("dateFilter").value = "";
        $("statusFilter").value = "all";

        renderReservations();
    }
);


// =========================================================
// ОТКРЫТИЕ ДЕТАЛЕЙ БРОНИ
// =========================================================

function openReservationDetails(id) {
    const reservation =
        reservations.find(
            (item) =>
                Number(item.id) === Number(id)
        );

    if (!reservation) {
        return;
    }

    selectedReservationId =
        reservation.id;

    $("detailsId").textContent =
        reservation.id;

    $("detailsName").textContent =
        reservation.customer_name;

    $("detailsPhone").textContent =
        reservation.phone;

    $("detailsTable").textContent =
        `Стол №${reservation.table_number}`;

    $("detailsGuests").textContent =
        reservation.guests;

    $("detailsDate").textContent =
        formatDate(
            reservation.reservation_date
        );

    $("detailsTime").textContent =
        reservation.reservation_time;

    const paymentStatus =
        reservation.payment_status || "unpaid";
       
    let paymentInfo =
        paymentText(paymentStatus);

    if (
        paymentStatus === "paid" &&
        reservation.payment_method
    ) {
        paymentInfo +=
            ` · ${paymentMethodText(
                reservation.payment_method
            )}`;
    }

    $("detailsPayment").textContent =
        paymentInfo;

    $("detailsPaidAt").textContent =
        reservation.paid_at || "—";

    $("detailsSpecialRequests").textContent =
        specialRequestsText(
            reservation.special_requests
        );

    $("detailsComment").textContent =
        reservation.comment || "—";

    $("detailsStatus").value =
        reservation.status;

    $("statusError").textContent =
        "";

    $("detailsModal").classList.add(
        "active"
    );
}


document.addEventListener(
    "click",
    (event) => {
        const button =
            event.target.closest(
                "[data-reservation-id]"
            );

        if (!button) {
            return;
        }

        openReservationDetails(
            Number(
                button.dataset.reservationId
            )
        );
    }
);


$("closeDetailsModal").addEventListener(
    "click",
    () => {
        $("detailsModal").classList.remove(
            "active"
        );
    }
);


$("detailsModal").addEventListener(
    "click",
    (event) => {
        if (
            event.target ===
            $("detailsModal")
        ) {
            $("detailsModal").classList.remove(
                "active"
            );
        }
    }
);


// =========================================================
// ИЗМЕНЕНИЕ СТАТУСА
// =========================================================

$("saveStatusButton").addEventListener(
    "click",
    async () => {
        if (!selectedReservationId) {
            return;
        }

        const status =
            $("detailsStatus").value;

        $("statusError").textContent =
            "";

        try {
            const response =
                await fetch(
                    `/api/reservations/${selectedReservationId}/status`,
                    {
                        method: "PATCH",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            status: status
                        })
                    }
                );

            const data =
                await response.json();

            if (!response.ok || !data.success) {
                $("statusError").textContent =
                    data.message ||
                    "Не удалось изменить статус.";

                return;
            }

            $("detailsModal").classList.remove(
                "active"
            );

            await loadReservations();

        } catch (error) {
            console.error(error);

            $("statusError").textContent =
                "Не удалось связаться с сервером.";
        }
    }
);


// =========================================================
// РЕДАКТИРОВАНИЕ БРОНИРОВАНИЯ
// =========================================================

$("openEditButton").addEventListener(
    "click",
    () => {
        const reservation =
            reservations.find(
                (item) =>
                    Number(item.id) ===
                    Number(selectedReservationId)
            );

        if (!reservation) {
            return;
        }

        $("detailsModal").classList.remove(
            "active"
        );

        $("editReservationNumber").textContent =
            reservation.id;

        $("editReservationId").value =
            reservation.id;

        $("editName").value =
            reservation.customer_name;

        $("editPhone").value =
            reservation.phone;

        $("editTable").value =
            reservation.table_number;

        $("editGuests").value =
            reservation.guests;

        $("editDate").value =
            reservation.reservation_date;

        $("editTime").value =
            reservation.reservation_time;

        $("editError").textContent =
            "";

        $("editModal").classList.add(
            "active"
        );
    }
);


$("closeEditModal").addEventListener(
    "click",
    () => {
        $("editModal").classList.remove(
            "active"
        );
    }
);


$("editModal").addEventListener(
    "click",
    (event) => {
        if (
            event.target ===
            $("editModal")
        ) {
            $("editModal").classList.remove(
                "active"
            );
        }
    }
);


$("editForm").addEventListener(
    "submit",
    async (event) => {
        event.preventDefault();

        const reservationId =
            Number(
                $("editReservationId").value
            );

        const payload = {
            customer_name:
                $("editName").value.trim(),

            phone:
                $("editPhone").value.trim(),

            table_number:
                Number($("editTable").value),

            guests:
                Number($("editGuests").value),

            reservation_date:
                $("editDate").value,

            reservation_time:
                $("editTime").value
        };

        $("editError").textContent = "";

        try {
            const response = await fetch(
                `/api/reservations/${reservationId}`,
                {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                }
            );

            const data = await response.json();

            if (!response.ok || !data.success) {
                $("editError").textContent =
                    data.message ||
                    "Не удалось сохранить изменения.";
                return;
            }

            $("editModal").classList.remove(
                "active"
            );

            await loadReservations();

        } catch (error) {
            console.error(error);
            $("editError").textContent =
                "Не удалось связаться с сервером.";
        }
    }
);
 
    
// =========================================================
// УПРАВЛЕНИЕ СТОЛИКАМИ
// =========================================================

async function loadTables() {
    try {
        const response = await fetch("/api/admin/tables");

        if (response.status === 401) {
            window.location.href = "/admin/login";
            return;
        }

        const data = await response.json();

        if (!response.ok || !data.success) {
            console.error(
                data.message || "Не удалось загрузить столики."
            );
            return;
        }

        restaurantTables = data.tables || [];

        renderTables();

    } catch (error) {
        console.error(
            "Ошибка загрузки столиков:",
            error
        );
    }
}


function getTableCharacteristics(tableNumber) {
    const characteristics = {
        1: "🪟 У окна",
        2: "🪟 У окна",
        3: "🪟 У окна",
        4: "🪟 У окна · 🔇 Тихая зона",
        5: "👶 Рядом с детской зоной",
        6: "👶 Рядом с детской зоной",
        7: "♿ Доступный стол · 🔇 Тихая зона",
        8: "👶 Рядом с детской зоной",
        9: "Обычный стол",
        10: "🔇 Тихая зона",
        11: "🌿 Терраса",
        12: "🌿 Терраса",
        13: "🌿 Терраса",
        14: "🌿 Терраса",
        15: "🌿 Терраса",
        16: "🌿 Терраса"
    };

    return characteristics[Number(tableNumber)] || "Стол ресторана";
}


function renderTables() {
    const container = $("adminTablesGrid");
    const empty = $("tablesEmpty");

    if (!container || !empty) {
        return;
    }

    container.innerHTML = "";

    const total = restaurantTables.length;

    const active = restaurantTables.filter(
        (table) => Boolean(Number(table.is_active))
    ).length;

    const disabled = total - active;

    if ($("tablesTotal")) {
        $("tablesTotal").textContent = total;
    }

    if ($("tablesActive")) {
        $("tablesActive").textContent = active;
    }

    if ($("tablesDisabled")) {
        $("tablesDisabled").textContent = disabled;
    }

    if (restaurantTables.length === 0) {
        empty.style.display = "block";
        return;
    }

    empty.style.display = "none";

    restaurantTables.forEach((table) => {
        const tableNumber = Number(table.table_number);
        const isActive = Boolean(Number(table.is_active));

        const card = document.createElement("article");

        card.className =
            `admin-table-card ${isActive ? "" : "is-disabled"}`;

        card.innerHTML = `
            <div class="table-card-top">

                <div class="admin-table-info">

                    <span class="table-number">
                        СТОЛ №${tableNumber}
                    </span>

                    <strong>
                        ${table.capacity} мест
                    </strong>

                    <span class="admin-table-characteristics">
                        ${getTableCharacteristics(tableNumber)}
                    </span>

                </div>

                <span class="table-state ${
                    isActive ? "active" : "disabled"
                }">
                    ${isActive ? "Доступен" : "Отключён"}
                </span>

            </div>

            <p>
                ${tableNumber <= 10 ? "Основной зал" : "Терраса"}
            </p>

            <button
                type="button"
                class="${
                    isActive
                        ? "disable-table-button"
                        : "enable-table-button"
                } table-toggle-button"
                data-table-number="${tableNumber}"
                data-table-active="${isActive}"
            >
                ${
                    isActive
                        ? "Сделать недоступным"
                        : "Сделать доступным"
                }
            </button>
        `;

        container.appendChild(card);
    });
}


document.addEventListener(
    "click",
    async (event) => {
        const button = event.target.closest(
            ".table-toggle-button"
        );

        if (!button) {
            return;
        }

        const tableNumber = Number(
            button.dataset.tableNumber
        );

        const currentlyActive =
            button.dataset.tableActive === "true";

        button.disabled = true;

        try {
            const response = await fetch(
                `/api/admin/tables/${tableNumber}/status`,
                {
                    method: "PATCH",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        is_active: !currentlyActive
                    })
                }
            );

            const data = await response.json();

            if (!response.ok || !data.success) {
                alert(
                    data.message ||
                    "Не удалось изменить статус столика."
                );

                button.disabled = false;
                return;
            }

            await loadTables();
            renderDashboard();

        } catch (error) {
            console.error(error);

            alert(
                "Не удалось связаться с сервером."
            );

            button.disabled = false;
        }
    }
);


// =========================================================
// ОТЧЁТЫ
// =========================================================

function getReportReservations() {
    const period = $("reportPeriod")
        ? $("reportPeriod").value
    
        : "all";

    if (period === "all") {
        return [...reservations];
    }

    const days = Number(period);

    if (!Number.isFinite(days)) {
        return [...reservations];
    }

    const now = new Date();

    const start = new Date();

    start.setHours(0, 0, 0, 0);

    start.setDate(
        start.getDate() - (days - 1)
    );

    return reservations.filter((reservation) => {
        const date = new Date(
            `${reservation.reservation_date}T00:00:00`
        );

        return date >= start && date <= now;
    });
}


function renderReports() {
    if (!$("reportsSection")) {
        return;
    }

    const data = getReportReservations();

    renderReportKpis(data);
    renderReportHighlights(data);
    renderDateChart(data);
    renderStatusReport(data);
    renderTableLoad(data);
}


function renderReportKpis(data) {
    const total = data.length;

    const guests = data.reduce(
        (sum, reservation) =>
            sum + Number(reservation.guests || 0),
        0
    );

    const completed = data.filter(
        (reservation) =>
            reservation.status === "completed"
    ).length;

    const cancelled = data.filter(
        (reservation) =>
            reservation.status === "cancelled"
    ).length;

    const cancelRate =
        total > 0
            ? Math.round(
                (cancelled / total) * 100
            )
            : 0;

    if ($("reportTotal")) {
        $("reportTotal").textContent = total;
    }

    if ($("reportGuests")) {
        $("reportGuests").textContent = guests;
    }

    if ($("reportCompleted")) {
        $("reportCompleted").textContent = completed;
    }

    if ($("reportCancelRate")) {
        $("reportCancelRate").textContent =
            `${cancelRate}%`;
    }
}


function renderReportHighlights(data) {
    const tableCounts = {};
    const timeCounts = {};

    let guestsTotal = 0;

    data.forEach((reservation) => {
        const table = Number(
            reservation.table_number
        );

        const time =
            reservation.reservation_time;

        tableCounts[table] =
            (tableCounts[table] || 0) + 1;

        timeCounts[time] =
            (timeCounts[time] || 0) + 1;

        guestsTotal += Number(
            reservation.guests || 0
        );
    });

    const popularTable = Object.entries(
        tableCounts
    ).sort(
        (a, b) => b[1] - a[1]
    )[0];

    const popularTime = Object.entries(
        timeCounts
    ).sort(
        (a, b) => b[1] - a[1]
    )[0];

    if ($("popularTable")) {
        $("popularTable").textContent =
            popularTable
                ? `№${popularTable[0]}`
                : "—";
    }

    if ($("popularTableText")) {
        $("popularTableText").textContent =
            popularTable
                ? `${popularTable[1]} бронирований`
                : "Нет данных";
    }

    if ($("popularTime")) {
        $("popularTime").textContent =
            popularTime
                ? popularTime[0]
                : "—";
    }

    if ($("popularTimeText")) {
        $("popularTimeText").textContent =
            popularTime
                ? `${popularTime[1]} бронирований`
                : "Нет данных";
    }

    if ($("averageGuests")) {
        $("averageGuests").textContent =
            data.length > 0
                ? (
                    guestsTotal /
                    data.length
                ).toFixed(1)
                : "0";
    }
}


function renderDateChart(data) {
    const container = $("dateChart");
    const empty = $("dateChartEmpty");

    if (!container || !empty) {
        return;
    }

    container.innerHTML = "";

    const counts = {};

    data.forEach((reservation) => {
        const date =
            reservation.reservation_date;

        counts[date] =
            (counts[date] || 0) + 1;
    });

    const entries = Object.entries(
        counts
    ).sort(
        (a, b) =>
            a[0].localeCompare(b[0])
    );

    if (entries.length === 0) {
        container.style.display = "none";
        empty.style.display = "block";
        return;
    }

    container.style.display = "flex";
    empty.style.display = "none";

    const max = Math.max(
        ...entries.map(
            (entry) => entry[1]
        ),
        1
    );

    entries.forEach(([date, count]) => {
        const column =
            document.createElement("div");

        column.className = "bar-column";

        const height = Math.max(
            4,
            Math.round(
                (count / max) * 160
            )
        );

        const dateObject = new Date(
            `${date}T00:00:00`
        );

        const label =
            dateObject.toLocaleDateString(
                "ru-RU",
                {
                    day: "2-digit",
                    month: "2-digit"
                }
            );

        column.innerHTML = `
            <span class="bar-value">
                ${count}
            </span>

            <div
                class="bar-fill"
                style="height:${height}px"
            ></div>

            <span class="bar-label">
                ${label}
            </span>
        `;

        container.appendChild(column);
    });
}


function renderStatusReport(data) {
    const container = $("statusReport");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    const statuses = [
        {
            key: "confirmed",
            label: "Подтверждено"
        },
        {
            key: "arrived",
            label: "Гость пришёл"
        },
        {
            key: "completed",
            label: "Завершено"
        },
        {
            key: "cancelled",
            label: "Отменено"
        }
    ];

    const total = data.length;

    statuses.forEach((status) => {
        const count = data.filter(
            (reservation) =>
                reservation.status === status.key
        ).length;

        const percent =
            total > 0
                ? Math.round((count / total) * 100)
                : 0;

        const row = document.createElement("div");

        row.className = "status-report-row";

        row.innerHTML = `
            <span>${status.label}</span>

            <div class="progress-track">
                <div
                    class="progress-fill"
                    style="width:${percent}%"
                ></div>
            </div>

            <strong>${count}</strong>
        `;

        container.appendChild(row);
    });
}


function renderTableLoad(data) {
    const container = $("tableLoad");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    const counts = {};

    for (let table = 1; table <= 16; table++) {
        counts[table] = 0;
    }

    data.forEach((reservation) => {
        const table = Number(
            reservation.table_number
        );

        if (counts[table] !== undefined) {
            counts[table] += 1;
        }
    });

    Object.entries(counts).forEach(
        ([table, count]) => {
            const card = document.createElement("div");

            card.className = "table-load-card";

            card.innerHTML = `
                <span>СТОЛ №${table}</span>
                <strong>${count}</strong>
                <small>бронирований</small>
            `;

            container.appendChild(card);
        }
    );
}


$("reportPeriod")?.addEventListener(
    "change",
    renderReports
);

 // =========================================================
 // ПРЕДЗАКАЗЫ
 // =========================================================

function preorderStatusText(status) {
    const statuses = {
        new: "Новый",
        preparing: "Готовится",
        ready: "Готов"
    };

    return statuses[status] || "Новый";
}


function preorderStatusClass(status) {
    const classes = {
        new: "preorder-status-new",
        preparing: "preorder-status-preparing",
        ready: "preorder-status-ready"
    };

    return (
        classes[status] ||
        "preorder-status-new"
    );
}


function getReservationsWithPreorder() {
    return reservations.filter(
        (reservation) =>
            Array.isArray(
                reservation.preorder_items
            ) &&
            reservation.preorder_items.length > 0
    );
}


function getPreorderTotal(reservation) {
    if (
        reservation.preorder_total !== null &&
        reservation.preorder_total !== undefined
    ) {
        return Number(
            reservation.preorder_total || 0
        );
    }

    if (
        !Array.isArray(
            reservation.preorder_items
        )
    ) {
        return 0;
    }

    return reservation.preorder_items.reduce(
        (sum, item) => {
            return (
                sum +
                Number(item.quantity || 0) *
                Number(item.unit_price || 0)
            );
        },
        0
    );
}


function getPreorderItemsQuantity(
    reservation
) {
    if (
        !Array.isArray(
            reservation.preorder_items
        )
    ) {
        return 0;
    }

    return reservation.preorder_items.reduce(
        (sum, item) =>
            sum +
            Number(item.quantity || 0),
        0
    );
}


function formatMoney(amount) {
    return (
        Number(amount || 0).toLocaleString(
            "ru-RU"
        ) + " ₸"
    );
}


function getFilteredPreorders() {
    const search = $("preorderSearch")
        ? $("preorderSearch")
            .value
            .trim()
            .toLowerCase()
        : "";

    const date = $("preorderDateFilter")
        ? $("preorderDateFilter").value
        : "";

    return getReservationsWithPreorder()
        .filter((reservation) => {
            const searchText = `
                ${reservation.id}
                ${reservation.customer_name}
                ${reservation.phone}
            `.toLowerCase();

            const matchesSearch =
                !search ||
                searchText.includes(search);

            const matchesDate =
                !date ||
                reservation.reservation_date ===
                    date;

            return (
                matchesSearch &&
                matchesDate
            );
        })
        .sort((a, b) => {
            const first =
                `${a.reservation_date} ${a.reservation_time}`;

            const second =
                `${b.reservation_date} ${b.reservation_time}`;

            return first.localeCompare(second);
        });
}


function renderPreorders() {
    const container =
        $("preordersList");

    if (!container) {
        return;
    }

    const empty =
        $("preordersEmpty");

    const allPreorders =
        getReservationsWithPreorder();

    const filtered =
        getFilteredPreorders();

    container.innerHTML = "";

    const totalItems =
        allPreorders.reduce(
            (sum, reservation) =>
                sum +
                getPreorderItemsQuantity(
                    reservation
                ),
            0
        );

    const totalAmount =
        allPreorders.reduce(
            (sum, reservation) =>
                sum +
                getPreorderTotal(
                    reservation
                ),
            0
        );

    if ($("preordersCount")) {
        $("preordersCount").textContent =
            allPreorders.length;
    }

    if ($("preordersItemsCount")) {
        $("preordersItemsCount").textContent =
            totalItems;
    }

    if ($("preordersAmount")) {
        $("preordersAmount").textContent =
            formatMoney(totalAmount);
    }

    if ($("preordersNavCount")) {
        $("preordersNavCount").textContent =
            allPreorders.length;
    }

    if (filtered.length === 0) {
        if (empty) {
            empty.style.display =
                "block";
        }

        return;
    }

    if (empty) {
        empty.style.display = "none";
    }

    filtered.forEach((reservation) => {
        const card =
            document.createElement("article");

        card.className =
            "preorder-admin-card";

        const itemsQuantity =
            getPreorderItemsQuantity(
                reservation
            );

        const total =
            getPreorderTotal(
                reservation
            );

        const kitchenStatus =
            reservation.preorder_status ||
            "new";

        card.innerHTML = `
            <div class="preorder-card-id">
                <span>Бронь</span>

                <strong>
                    #${reservation.id}
                </strong>
            </div>

            <div class="preorder-card-client">
                <strong>
                    ${reservation.customer_name}
                </strong>

                <span>
                    ${reservation.phone}
                </span>
            </div>

            <div class="preorder-card-meta">
                <strong>
                    Стол №${reservation.table_number}
                </strong>

                <span>
                    ${reservation.guests} гост.
                </span>
            </div>

            <div class="preorder-card-date">
                <strong>
                    ${formatDate(
                        reservation.reservation_date
                    )}
                </strong>

                <span>
                    ${reservation.reservation_time}
                </span>
            </div>

            <div class="preorder-card-items">
                <strong>
                    ${itemsQuantity}
                </strong>

                <span>блюд</span>
            </div>

            <div class="preorder-card-total">
                <strong>
                    ${formatMoney(total)}
                </strong>

                <span
                    class="preorder-status ${preorderStatusClass(
                        kitchenStatus
                    )}"
                >
                    ${preorderStatusText(
                        kitchenStatus
                    )}
                </span>
            </div>

            <button
                type="button"
                class="view-button preorder-details-button"
                data-preorder-id="${reservation.id}"
            >
                Подробнее
            </button>
        `;

        container.appendChild(card);
    });
}


if ($("preorderSearch")) {
    $("preorderSearch").addEventListener(
        "input",
        renderPreorders
    );
}


if ($("preorderDateFilter")) {
    $("preorderDateFilter").addEventListener(
        "change",
        renderPreorders
    );
}


if ($("resetPreorderFilters")) {
    $("resetPreorderFilters").addEventListener(
        "click",
        () => {
            $("preorderSearch").value = "";
            $("preorderDateFilter").value = "";

            renderPreorders();
        }
    );
}


// =========================================================
// ДЕТАЛИ ПРЕДЗАКАЗА
// =========================================================

let selectedPreorderId = null;


function openPreorderDetails(id) {
    const reservation =
        reservations.find(
            (item) =>
                Number(item.id) === Number(id)
        );

    if (
        !reservation ||
        !Array.isArray(
            reservation.preorder_items
        ) ||
        reservation.preorder_items.length === 0
    ) {
        return;
    }

    selectedPreorderId =
        reservation.id;

    if ($("preorderDetailsId")) {
        $("preorderDetailsId").textContent =
            reservation.id;
    }

    if ($("preorderDetailsName")) {
        $("preorderDetailsName").textContent =
            reservation.customer_name;
    }

    if ($("preorderDetailsPhone")) {
        $("preorderDetailsPhone").textContent =
            reservation.phone;
    }

    if ($("preorderDetailsTable")) {
        $("preorderDetailsTable").textContent =
            `Стол №${reservation.table_number}`;
    }

    if ($("preorderDetailsGuests")) {
        $("preorderDetailsGuests").textContent =
            reservation.guests;
    }

    if ($("preorderDetailsDate")) {
        $("preorderDetailsDate").textContent =
            formatDate(
                reservation.reservation_date
            );
    }

    if ($("preorderDetailsTime")) {
        $("preorderDetailsTime").textContent =
            reservation.reservation_time;
    }

    if ($("preorderDetailsStatus")) {
        $("preorderDetailsStatus").textContent =
            statusText(
                reservation.status
            );
    }

    if ($("preorderDetailsTotal")) {
        $("preorderDetailsTotal").textContent =
            formatMoney(
                getPreorderTotal(
                    reservation
                )
            );
    }

    if ($("preorderDetailsRequests")) {
        $("preorderDetailsRequests").textContent =
            specialRequestsText(
                reservation.special_requests
            );
    }

    if ($("preorderDetailsComment")) {
        $("preorderDetailsComment").textContent =
            reservation.comment || "—";
    }

    const itemsContainer =
        $("preorderDetailsItems");

    if (itemsContainer) {
        itemsContainer.innerHTML = "";

        reservation.preorder_items.forEach(
            (item) => {
                const row =
                    document.createElement(
                        "div"
                    );

                row.className =
                    "preorder-details-row";

                const quantity =
                    Number(
                        item.quantity || 0
                    );

                const unitPrice =
                    Number(
                        item.unit_price || 0
                    );

                const itemTotal =
                    item.total !== undefined &&
                    item.total !== null

                        ? Number(item.total)
                        : quantity * unitPrice;

                row.innerHTML = `
                    <div>
                        <strong>
                            ${item.name}
                        </strong>

                        <span>
                            ${item.category || ""}
                        </span>
                    </div>

                    <div class="preorder-details-calculation">
                        <span>
                            ${quantity}
                            ×
                            ${formatMoney(unitPrice)}
                        </span>

                        <strong>
                            ${formatMoney(itemTotal)}
                        </strong>
                    </div>
                `;

                itemsContainer.appendChild(
                    row
                );
            }
        );
    }

    const currentStatus =
        reservation.preorder_status ||
        "new";

    if ($("preorderStatusSelect")) {
        $("preorderStatusSelect").value =
            currentStatus;
    }

    if ($("preorderDetailsKitchenStatus")) {
        $("preorderDetailsKitchenStatus").innerHTML = `
            <span
                class="preorder-status ${preorderStatusClass(
                    currentStatus
                )}"
            >
                ${preorderStatusText(
                    currentStatus
                )}
            </span>
        `;
    }

    if ($("preorderStatusError")) {
        $("preorderStatusError").textContent =
            "";
    }

    if ($("preorderDetailsModal")) {
        $("preorderDetailsModal")
            .classList.add("active");
    }
}


document.addEventListener(
    "click",
    (event) => {
        const button =
            event.target.closest(
                ".preorder-details-button"
            );

        if (!button) {
            return;
        }

        openPreorderDetails(
            Number(
                button.dataset.preorderId
            )
        );
    }
);


if ($("closePreorderDetailsModal")) {
    $("closePreorderDetailsModal")
        .addEventListener(
            "click",
            () => {
                $("preorderDetailsModal")
                    .classList.remove(
                        "active"
                    );

                selectedPreorderId =
                    null;
            }
        );
}

if ($("preorderDetailsModal")) {
    $("preorderDetailsModal")
        .addEventListener(
            "click",
            (event) => {
                if (
                    event.target ===
                    $("preorderDetailsModal")
                ) {
                    $("preorderDetailsModal")
                        .classList.remove(
                            "active"
                        );

                    selectedPreorderId =
                        null;
                }
            }
        );
}


// =========================================================
// СТАТУС ПРЕДЗАКАЗА
// =========================================================


if ($("savePreorderStatusButton")) {
    $("savePreorderStatusButton").addEventListener(
        "click",
        async () => {
            if (!selectedPreorderId) {
                return;
            }

            const select = $("preorderStatusSelect");

            if (!select) {
                return;
            }

            const newStatus = select.value;

            if ($("preorderStatusError")) {
                $("preorderStatusError").textContent = "";
            }

            try {
                const response = await fetch(
                    `/api/admin/reservations/${selectedPreorderId}/preorder-status`,
                    {
                        method: "PATCH",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            status: newStatus
                        })
                    }
                );

                const data = await response.json();

                if (!response.ok || !data.success) {
                    if ($("preorderStatusError")) {
                        $("preorderStatusError").textContent =
                            data.message ||
                            "Не удалось изменить статус.";
                    }

                    return;
                }

                const reservation = reservations.find(
                    (item) =>
                        Number(item.id) ===
                        Number(selectedPreorderId)
                );

                if (reservation) {
                    reservation.preorder_status =
                        data.preorder_status || newStatus;
                }

                renderPreorders();
                renderDashboard();

                openPreorderDetails(selectedPreorderId);

            } catch (error) {
                console.error(error);

                if ($("preorderStatusError")) {
                    $("preorderStatusError").textContent =
                        "Не удалось связаться с сервером.";
                }
            }
        }
    );
}

function renderDashboard() {
    const section = $("dashboardSection");

    if (!section) {
        return;
    }

    renderDashboardKpis();
    renderDashboardBookingsChart();
    renderDashboardStatuses();
    renderDashboardZones();
    renderDashboardPopularTables();
    renderDashboardPopularTimes();
    renderDashboardUpcoming();
    renderDashboardRecentPreorders();
}

function setTextIfExists(id, value) {
    const element = $(id);

    if (element) {
        element.textContent = value;
    }
}

function renderDashboardKpis() {
    const today =
        getTodayString();

    const todayReservations =
        reservations.filter(
            (reservation) =>
                reservation.reservation_date ===
                today
        );

    const todayGuests =
        todayReservations
            .filter(
                (reservation) =>
                    reservation.status !==
                    "cancelled"
            )
            .reduce(
                (sum, reservation) =>
                    sum +
                    Number(
                        reservation.guests ||
                        0
                    ),
                0
            );

    const activeBookings =
        reservations.filter(
            (reservation) =>
                reservation.status ===
                    "confirmed" ||
                reservation.status ===
                    "arrived"
        ).length;

    const cancelled =
        reservations.filter(
            (reservation) =>
                reservation.status ===
                "cancelled"
        ).length;

    const preorders =
        getReservationsWithPreorder();

    const preorderAmount =
        preorders.reduce(
            (sum, reservation) =>
                sum +
                getPreorderTotal(
                    reservation
                ),
            0
        );

    const paidDeposits =
        reservations.filter(
            (reservation) =>
                reservation.payment_status ===
                "paid"
        ).length;

    const activeTables =
        restaurantTables.filter(
            (table) =>
                Boolean(
                    Number(
                        table.is_active
                    )
                )
        ).length;

    setTextIfExists(
        "dashboardTodayBookings",
        todayReservations.length
    );

    setTextIfExists(
        "dashboardTodayGuests",
        todayGuests
    );

    setTextIfExists(
        "dashboardActiveBookings",
        activeBookings
    );

    setTextIfExists(
        "dashboardCancelledBookings",
        cancelled
    );

    setTextIfExists(
        "dashboardPreorders",
        preorders.length
    );

    setTextIfExists(
        "dashboardPreorderAmount",
        formatMoney(
            preorderAmount
        )
    );

    setTextIfExists(
        "dashboardPaidDeposits",
        paidDeposits
    );

    setTextIfExists(
        "dashboardAvailableTables",
        restaurantTables.length
            ? `${activeTables} / ${restaurantTables.length}`
            : "—"
    );
}


function getLastSevenDays() {
    const days = [];

    const today = new Date();

    today.setHours(
        0,
        0,
        0,
        0
    );

    for (
        let offset = 6;
        offset >= 0;
        offset -= 1
    ) {
        const date =
            new Date(today);

        date.setDate(
            today.getDate() -
            offset
        );

        const year =
            date.getFullYear();

        const month =
            String(
                date.getMonth() + 1
            ).padStart(
                2,
                "0"
            );

        const day =
            String(
                date.getDate()
            ).padStart(
                2,
                "0"
            );

        days.push({
            key:
                `${year}-${month}-${day}`,

            label:
                date.toLocaleDateString(
                    "ru-RU",
                    {
                        day: "2-digit",
                        month: "2-digit"
                    }
                )
        });
    }

    return days;
}

function renderDashboardBookingsChart() {
    const container =
        $("dashboardBookingChart");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    const days =
        getLastSevenDays();

    const counts =
        days.map((day) => {
            return reservations.filter(
                (reservation) =>
                    reservation.reservation_date ===
                    day.key
            ).length;
        });

    const max =
        Math.max(
            ...counts,
            1
        );

    days.forEach(
        (day, index) => {
            const count =
                counts[index];

            const column =
                document.createElement(
                    "div"
                );

            column.className =
                "dashboard-chart-column";

            const height =
                Math.max(
                    count > 0
                        ? 12
                        : 3,

                    Math.round(
                        (count / max) *
                        150
                    )
                );

            column.innerHTML = `
                <strong>
                    ${count}
                </strong>

                <div
                    class="dashboard-chart-bar"
                    style="height:${height}px"
                ></div>

                <span>
                    ${day.label}
                </span>
            `;

            container.appendChild(
                column
            );
        }
    );
}

function renderDashboardStatuses() {
    const container =
        $("dashboardStatuses");

    if (!container) {
        return;
    }

    const counts = {
        confirmed: reservations.filter(
            (r) => r.status === "confirmed"
        ).length,

        arrived: reservations.filter(
            (r) => r.status === "arrived"
        ).length,

        completed: reservations.filter(
            (r) => r.status === "completed"
        ).length,

        cancelled: reservations.filter(
            (r) => r.status === "cancelled"
        ).length
    };

    const total =
        reservations.length || 1;

    const confirmedPercent =
        (counts.confirmed / total) * 100;

    const arrivedPercent =
        (counts.arrived / total) * 100;

    const completedPercent =
        (counts.completed / total) * 100;

    const confirmedEnd =
        confirmedPercent;

    const arrivedEnd =
        confirmedEnd +
        arrivedPercent;

    const completedEnd =
        arrivedEnd +
        completedPercent;

    container.innerHTML = `
        <div
            class="dashboard-status-donut"
            style="
                background:
                conic-gradient(
                    #b58a52 0%
                    ${confirmedEnd}%,

                    #6e9278
                    ${confirmedEnd}%
                    ${arrivedEnd}%,

                    #7f7b76
                    ${arrivedEnd}%
                    ${completedEnd}%,

                    #b86861
                    ${completedEnd}%
                    100%
                );
            "
        >
            <div class="dashboard-status-center">
                <strong>
                    ${reservations.length}
                </strong>

                <span>
                    всего
                </span>
            </div>
        </div>

        <div class="dashboard-status-legend">

            <div class="dashboard-status-legend-row">
                <span class="dashboard-status-dot confirmed"></span>

                <span>
                    Подтверждено
                </span>

                <strong>
                    ${counts.confirmed}
                </strong>
            </div>

            <div class="dashboard-status-legend-row">
                <span class="dashboard-status-dot arrived"></span>

                <span>
                    Гость пришёл
                </span>

                <strong>
                    ${counts.arrived}
                </strong>
            </div>

            <div class="dashboard-status-legend-row">
                <span class="dashboard-status-dot completed"></span>

                <span>
                    Завершено
                </span>

                <strong>
                    ${counts.completed}
                </strong>
            </div>

            <div class="dashboard-status-legend-row">
                <span class="dashboard-status-dot cancelled"></span>

                <span>
                    Отменено
                </span>

                <strong>
                    ${counts.cancelled}
                </strong>
            </div>

        </div>
    `;
}

function renderDashboardZones() {
    const container =
        $("dashboardZones");

    if (!container) {
        return;
    }

    const hall =
        reservations.filter(
            (reservation) =>
                Number(
                    reservation.table_number
                ) <= 10
        ).length;

    const terrace =
        reservations.filter(
            (reservation) =>
                Number(
                    reservation.table_number
                ) >= 11
        ).length;

    const total =
        hall + terrace;

    const hallPercent =
        total > 0
            ? Math.round(
                (hall / total) * 100
            )
            : 0;

    const terracePercent =
        total > 0
            ? 100 - hallPercent
            : 0;

    container.innerHTML = `
        <div
            class="dashboard-zone-donut"
            style="
                background:
                conic-gradient(
                    #a67b45
                    0%
                    ${hallPercent}%,

                    #78906d
                    ${hallPercent}%
                    100%
                );
            "
        >
            <div class="dashboard-zone-center">

                <strong>
                    ${total}
                </strong>

                <span>
                    броней
                </span>

            </div>
        </div>

        <div class="dashboard-zone-legend">

            <div class="dashboard-zone-legend-row">

                <span class="dashboard-zone-dot hall"></span>

                <div>
                    <strong>
                        Зал
                    </strong>

                    <span>
                        ${hall} бронирований
                    </span>
                </div>

                <strong>
                    ${hallPercent}%
                </strong>

            </div>

            <div class="dashboard-zone-legend-row">

                <span class="dashboard-zone-dot terrace"></span>

                <div>
                    <strong>
                        Терраса
                    </strong>

                    <span>
                        ${terrace} бронирований
                    </span>
                </div>

                <strong>
                    ${terracePercent}%
                </strong>

            </div>

        </div>
    `;
}

function renderDashboardPopularTables() {
    const container =
        $("dashboardPopularTables");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    const counts = {};

    reservations.forEach(
        (reservation) => {
            const table =
                Number(
                    reservation.table_number
                );

            counts[table] =
                (counts[table] || 0) + 1;
        }
    );

    const entries =
        Object.entries(counts)
            .sort(

                (a, b) =>
                    b[1] - a[1]
            )
            .slice(0, 5);

    if (!entries.length) {
        container.innerHTML =
            `<p class="dashboard-empty">Нет данных</p>`;

        return;
    }

    const max =
        Math.max(
            ...entries.map(
                (entry) =>
                    entry[1]
            ),
            1
        );

    entries.forEach(
        ([table, count], index) => {

            const percent =
                Math.round(
                    (count / max) * 100
                );

            const row =
                document.createElement(
                    "div"
                );

            row.className =
                "dashboard-ranking-row";

            row.innerHTML = `
                <span class="dashboard-rank">
                    ${index + 1}
                </span>

                <div class="dashboard-ranking-info">
                    <strong>
                        Стол №${table}
                    </strong>

                    <small>
                        ${getTableCharacteristics(
                            Number(table)
                        )}
                    </small>
                </div>

                <div class="dashboard-ranking-bar-track">

                    <div
                        class="dashboard-ranking-bar"
                        style="width:${percent}%"
                    ></div>

                </div>

                <span class="dashboard-ranking-count">
                    ${count}
                </span>
            `;

            container.appendChild(
                row
            );
        }
    );
}

function renderDashboardPopularTimes() {
    const container =
        $("dashboardPopularTimes");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    const counts = {};

    reservations.forEach(
        (reservation) => {
            const time =
                reservation.reservation_time;

            counts[time] =
                (counts[time] || 0) + 1;
        }
    );

    const entries =
        Object.entries(counts)
            .sort(
                (a, b) =>
                    b[1] - a[1]
            )
            .slice(0, 5);

    if (!entries.length) {
        container.innerHTML =
            `<p class="dashboard-empty">Нет данных</p>`;

        return;
    }

    const max =
        Math.max(
            ...entries.map(
                (entry) =>
                    entry[1]
            ),
            1
        );

    entries.forEach(
        ([time, count], index) => {

            const percent =
                Math.round(
                    (count / max) * 100
                );

            const row =
                document.createElement(
                    "div"
                );

            row.className =
                "dashboard-ranking-row";

            row.innerHTML = `
                <span class="dashboard-rank">
                    ${index + 1}
                </span>

                <div class="dashboard-ranking-info">
                    <strong>
                        ${time}
                    </strong>

                    <small>
                        Время бронирования
                    </small>
                </div>

                <div class="dashboard-ranking-bar-track">

                    <div
                        class="dashboard-ranking-bar"
                        style="width:${percent}%"
                    ></div>

                </div>

                <span class="dashboard-ranking-count">
                    ${count}
                </span>
            `;

            container.appendChild(
                row
            );
        }
    );
}

function renderDashboardUpcoming() {
    const container =
        $("dashboardUpcoming");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    const now =
        new Date();

    const upcoming =
        reservations
            .filter(
                (reservation) => {
                    if (
                        reservation.status ===
                            "cancelled" ||
                        reservation.status ===
                            "completed"
                    ) {
                        return false;
                    }

                    const date =
                        new Date(
                            `${reservation.reservation_date}T${reservation.reservation_time}:00`
                        );

                    return date >= now;
                }
            )
            .sort(
                (a, b) => {
                    const first =
                        `${a.reservation_date} ${a.reservation_time}`;

                    const second =
                        `${b.reservation_date} ${b.reservation_time}`;

                    return first.localeCompare(
                        second
                    );
                }
            )
            .slice(
                0,
                6
            );

    if (!upcoming.length) {
        container.innerHTML =
            `<p class="dashboard-empty">Ближайших броней нет</p>`;

        return;
    }

    upcoming.forEach(
        (reservation) => {
            const card =
                document.createElement(
                    "button"
                );

            card.type =
                "button";

            card.className =
                "dashboard-upcoming-card";

            card.dataset.reservationId =
                reservation.id;

            card.innerHTML = `
                <div>
                    <strong>
                        ${reservation.customer_name}
                    </strong>

                    <span>
                        ${formatDate(
                            reservation.reservation_date
                        )}
                        ·
                        ${reservation.reservation_time}
                    </span>
                </div>

                <div>
                    <strong>
                        Стол №${reservation.table_number}
                    </strong>

                    <span>
                        ${reservation.guests} гост.
                    </span>
                </div>
            `;

            container.appendChild(
                card
            );
        }
    );
}


function renderDashboardRecentPreorders() {
    const container =
        $("dashboardRecentPreorders");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    const preorders =
        getReservationsWithPreorder()
            .sort(
                (a, b) => {
                    const first =
                        `${a.reservation_date} ${a.reservation_time}`;

                    const second =
                        `${b.reservation_date} ${b.reservation_time}`;

                    return second.localeCompare(
                        first
                    );
                }
            )
            .slice(
                0,
                5
            );

    if (!preorders.length) {
        container.innerHTML =
            `<p class="dashboard-empty">Предзаказов пока нет</p>`;

        return;
    }

    preorders.forEach(
        (reservation) => {
            const card =
                document.createElement(
                    "button"
                );

            card.type =
                "button";

            card.className =
                "dashboard-preorder-card preorder-details-button";

            card.dataset.preorderId =
                reservation.id;

            const status =
                reservation.preorder_status ||
                "new";

            card.innerHTML = `
                <div>
                    <strong>
                        ${reservation.customer_name}
                    </strong>

                    <span>
                        Бронь #${reservation.id}
                        ·
                        Стол №${reservation.table_number}
                    </span>
                </div>

                <div>
                    <strong>
                        ${formatMoney(
                            getPreorderTotal(
                                reservation
                            )
                        )}
                    </strong>

                    <span
                        class="preorder-status ${preorderStatusClass(
                            status
                        )}"
                    >
                        ${preorderStatusText(
                            status
                        )}
                    </span>
                </div>
            `;

            container.appendChild(
                card
            );
        }
    );
}


// =========================================================
// ESC
// =========================================================

document.addEventListener(
    "keydown",
    (event) => {
        if (event.key !== "Escape") {
            return;
        }

        if ($("detailsModal")) {
            $("detailsModal")
                .classList.remove(
                    "active"
                );
        }

        if ($("editModal")) {
            $("editModal")
                .classList.remove(
                    "active"
                );
        }

        if ($("preorderDetailsModal")) {
            $("preorderDetailsModal")
                .classList.remove(
                    "active"
                );
        }
    }
);

// =========================================================
// ЖУРНАЛ ДЕЙСТВИЙ АДМИНИСТРАТОРА
// =========================================================
function adminLogActionText(actionType) {
    const labels = {
        reservation_edited: "Редактирование брони",
        reservation_status_changed: "Статус брони",
        reservation_cancelled: "Отмена брони",
        preorder_status_changed: "Статус предзаказа",
        table_status_changed: "Статус столика"
    };
    return labels[actionType] || actionType || "Действие";
}

function adminLogEntityText(log) {
    if (log.entity_type === "reservation") return `Бронь #${log.entity_id ?? "—"}`;
    if (log.entity_type === "table") return `Стол №${log.entity_id ?? "—"}`;
    return log.entity_id ? `${log.entity_type || "Объект"} #${log.entity_id}` : (log.entity_type || "—");
}

function adminLogValueText(value, actionType) {
    if (value === null || value === undefined || value === "") return "—";
    if (actionType === "reservation_status_changed" || actionType === "reservation_cancelled") return statusText(value);
    if (actionType === "preorder_status_changed") return preorderStatusText(value);
    if (actionType === "table_status_changed") {
        const values = { active: "Доступен", inactive: "Недоступен" };
        return values[value] || value;
    }
    return String(value);
}

function formatAdminLogDate(value) {
    if (!value) return "—";
    const date = new Date(String(value).replace(" ", "T") + "Z");
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString("ru-RU", {
        day: "2-digit", month: "2-digit", year: "numeric",
        hour: "2-digit", minute: "2-digit"
    });
}

async function loadAdminLogs() {
    try {
        const response = await fetch("/api/admin/logs?limit=500");
        if (response.status === 401) {
            window.location.href = "/admin/login";
            return;
        }
        const data = await response.json();
        if (!response.ok || !data.success) {
            console.error(data.message || "Не удалось загрузить журнал действий.");
            return;
        }
        adminLogs = data.logs || [];
        renderAdminLogs();
    } catch (error) {
        console.error("Ошибка загрузки журнала действий:", error);
    }
}

function getFilteredAdminLogs() {
    const search = ($("logsSearch")?.value || "").trim().toLowerCase();
    const action = $("logsActionFilter")?.value || "all";
    return adminLogs.filter((log) => {
        if (action !== "all" && log.action_type !== action) return false;
        if (!search) return true;
        const searchable = [
            log.admin_username, log.description, log.action_type, log.entity_type,
            log.entity_id, log.old_value, log.new_value,
            adminLogActionText(log.action_type), adminLogEntityText(log)
        ].filter((v) => v !== null && v !== undefined).join(" ").toLowerCase();
        return searchable.includes(search);
    });
}

function renderAdminLogs() {
    const table = $("logsTable");
    const empty = $("logsEmpty");
    if (!table || !empty) return;

    const filtered = getFilteredAdminLogs();
    if ($("logsTotal")) $("logsTotal").textContent = adminLogs.length;

    const now = new Date();
    const todayCount = adminLogs.filter((log) => {
        if (!log.created_at) return false;
        const d = new Date(String(log.created_at).replace(" ", "T") + "Z");
        return !Number.isNaN(d.getTime()) &&
            d.getFullYear() === now.getFullYear() &&
            d.getMonth() === now.getMonth() &&
            d.getDate() === now.getDate();
    }).length;

    if ($("logsToday")) $("logsToday").textContent = todayCount;
    if ($("logsAdmin")) $("logsAdmin").textContent = adminLogs[0]?.admin_username || "admin";

    table.innerHTML = "";
    if (filtered.length === 0) {
        empty.style.display = "block";
        return;
    }
    empty.style.display = "none";

    filtered.forEach((log) => {
        const row = document.createElement("tr");
        const oldText = adminLogValueText(log.old_value, log.action_type);
        const newText = adminLogValueText(log.new_value, log.action_type);
        let changeHtml = `<span class="log-description">${log.description || "—"}</span>`;
        if (log.old_value !== null || log.new_value !== null) {
            changeHtml += `<div class="log-change"><span class="log-old">${oldText}</span><span class="log-arrow">→</span><span class="log-new">${newText}</span></div>`;
        }
        row.innerHTML = `
            <td class="log-date">${formatAdminLogDate(log.created_at)}</td>
            <td><strong>${log.admin_username || "admin"}</strong></td>
            <td><span class="log-action log-action-${log.action_type || "default"}">${adminLogActionText(log.action_type)}</span></td>
            <td>${adminLogEntityText(log)}</td>
            <td>${changeHtml}</td>
        `;
        table.appendChild(row);
    });
}

$("logsSearch")?.addEventListener("input", renderAdminLogs);
$("logsActionFilter")?.addEventListener("change", renderAdminLogs);
$("resetLogsFilters")?.addEventListener("click", () => {
    if ($("logsSearch")) $("logsSearch").value = "";
    if ($("logsActionFilter")) $("logsActionFilter").value = "all";
    renderAdminLogs();
});
$("refreshLogsButton")?.addEventListener("click", loadAdminLogs);


// =========================================================
// ЗАПУСК АДМИН-ПАНЕЛИ
// =========================================================

async function initializeAdmin() {
    await loadTables();
    await loadReservations();
    await loadAdminLogs();

    renderReports();
    renderDashboard();
}


initializeAdmin();
