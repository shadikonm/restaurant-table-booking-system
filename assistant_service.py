"""FAQ assistant with optional LLM backend. No user data or booking details sent."""

import json
import os
from urllib.request import Request, urlopen

SYSTEM_PROMPT = (
    "Ты помощник ресторана TABLE. Отвечай кратко на языке вопроса (русский, қазақша, English). "
    "Помогай только с бронированием, выбором столов и меню. "
    "Не утверждай, что бронь создана, отменена или что стол свободен без проверки. "
    "Для бронирования направляй пользователя к форме на сайте. "
    "Используй только предоставленное меню; не выдумывай блюда и цены. "
    "Не проси пароль, телефон, email и платёжные данные."
)


def local_answer(question, menu):
    q = question.lower().strip()
    kk = any(
        x in q for x in ("қалай", "үстел", "мәзір", "брондау", "тапсырыс", "сәлем")
    )
    en = (
        any(
            x in q
            for x in (
                "hello",
                "book",
                "reserve",
                "table",
                "menu",
                "cancel",
                "food",
                "price",
            )
        )
        and not kk
    )
    if any(
        x in q
        for x in (
            "меню",
            "мәзір",
            "menu",
            "блюд",
            "еда",
            "food",
            "цена",
            "price",
            "тағам",
        )
    ):
        if not menu:
            return "Меню пока недоступно. Пожалуйста, попробуйте позже."
        dishes = "; ".join(f"{x['name']} — {x['price']} ₸" for x in menu[:10])
        intro = (
            "Мәзірден тағамдар: "
            if kk
            else ("Menu items: " if en else "Примеры блюд из меню: ")
        )
        return (
            intro
            + dishes
            + (". Полный список — в форме бронирования." if not kk and not en else ".")
        )
    if any(x in q for x in ("отмен", "cancel", "болдырма")):
        return (
            "Брондауды жеке кабинетте тоқтатуға болады."
            if kk
            else "You can cancel an eligible reservation in your account."
            if en
            else "Отменить доступное для отмены бронирование можно в личном кабинете."
        )
    if any(
        x in q
        for x in (
            "террас",
            "terrace",
            "зал",
            "hall",
            "үстел",
            "стол",
            "table",
            "мест",
            "seat",
        )
    ):
        return (
            "10 үстел залда, 6 үстел террасада. Бос орындарды күн мен уақытты таңдағаннан кейін тексеріңіз."
            if kk
            else "There are 10 tables indoors and 6 on the terrace. Select a date and time to check availability."
            if en
            else "В зале 10 столиков, на террасе 6. Выберите дату и время в форме, чтобы проверить доступность."
        )
    return (
        "Брондау үшін күнді, уақытты, қонақ санын және үстелді таңдаңыз. Мәзір туралы да сұрай аласыз."
        if kk
        else "To book, choose a date, time, guest count and table in the booking form. I can also help with the menu."
        if en
        else "Чтобы забронировать стол, выберите дату, время, количество гостей и столик в форме на главной странице. Также могу подсказать по меню и отмене брони."
    )


def answer_question(question, menu):
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if key:
        try:
            # Only send the user's assistant question and public menu, never account data.
            body = json.dumps(
                {
                    "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                    "messages": [
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT
                            + "\nМеню: "
                            + json.dumps(menu, ensure_ascii=False),
                        },
                        {"role": "user", "content": question},
                    ],
                    "max_tokens": 350,
                    "temperature": 0.2,
                }
            ).encode("utf-8")
            req = Request(
                "https://api.openai.com/v1/chat/completions",
                data=body,
                headers={
                    "Authorization": "Bearer " + key,
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urlopen(req, timeout=8) as response:
                data = json.load(response)
            text = data["choices"][0]["message"]["content"].strip()
            if text:
                return {"answer": text, "mode": "ai"}
        except Exception:
            # Do not expose provider errors or keys to visitors.
            pass
    return {"answer": local_answer(question, menu), "mode": "faq"}
