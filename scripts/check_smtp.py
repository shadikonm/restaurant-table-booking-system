"""Safe SMTP connection/authentication check. No emails are sent unless --send-to is supplied."""

import argparse
import os
import smtplib
import ssl
from email.message import EmailMessage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send-to", help="Explicit recipient for one test message")
    args = parser.parse_args()
    host = os.getenv("SMTP_HOST")
    sender = os.getenv("SMTP_FROM")
    if not host or not sender:
        raise SystemExit("Set SMTP_HOST and SMTP_FROM first; see docs/FINAL_SETUP.md")
    ssl_mode = os.getenv("SMTP_SSL", "0") == "1"
    port = int(os.getenv("SMTP_PORT", "465" if ssl_mode else "587"))
    server = (
        smtplib.SMTP_SSL(host, port, timeout=10, context=ssl.create_default_context())
        if ssl_mode
        else smtplib.SMTP(host, port, timeout=10)
    )
    with server:
        if not ssl_mode:
            server.starttls(context=ssl.create_default_context())
        if os.getenv("SMTP_USER"):
            server.login(os.environ["SMTP_USER"], os.getenv("SMTP_PASSWORD", ""))
        if args.send_to:
            message = EmailMessage()
            message["From"] = sender
            message["To"] = args.send_to
            message["Subject"] = "TABLE: проверка SMTP"
            message.set_content("Тестовое сообщение от приложения TABLE.")
            server.send_message(message)
            print("SMTP accepted the test message; inbox delivery is not guaranteed.")
        else:
            print("SMTP connection and authentication succeeded. No email sent.")


if __name__ == "__main__":
    main()
