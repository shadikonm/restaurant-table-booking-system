"""Run with python -m unittest discover -s tests -v; uses isolated temporary DB."""

import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SECRET_KEY", "unit-test-only-secret-key")
import app as project


class RestaurantTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.database = str(Path(self.tmp.name) / "test.db")
        self.old_db = project.DATABASE
        project.DATABASE = self.database
        project.app.config.update(TESTING=True)
        project.init_db()
        self.client = project.app.test_client()
        self.future = datetime.now() + timedelta(days=4)
        self.date = self.future.strftime("%Y-%m-%d")
        self.time = "18:00"
        self.mail = patch.object(project, "send_booking_email", return_value=True)
        self.mail.start()
        with self.client.session_transaction() as sess:
            sess["_csrf_token"] = "test-token"

    def tearDown(self):
        self.mail.stop()
        project.DATABASE = self.old_db
        self.tmp.cleanup()

    def post(self, url, **kwargs):
        headers = kwargs.pop("headers", {})
        with self.client.session_transaction() as sess:
            headers["X-CSRF-Token"] = sess["_csrf_token"]
        return self.client.post(url, headers=headers, **kwargs)

    def booking_data(self):
        return {
            "customer_name": "Test Guest",
            "phone": "+77071234567",
            "table_number": 1,
            "guests": 2,
            "reservation_date": self.date,
            "reservation_time": self.time,
            "special_requests": [],
            "preorder": [],
        }

    def test_home_and_health(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/health").json["status"], "ok")

    def test_registration_and_login(self):
        data = {
            "name": "Test User",
            "phone": "+77071234567",
            "email": "test@example.com",
            "password": "Pass12345!",
            "password2": "Pass12345!",
            "csrf_token": "test-token",
        }
        result = self.post("/register", data=data)
        self.assertEqual(result.status_code, 302)
        self.assertIn("/account", result.location)
        self.client.get("/logout")
        result = self.post(
            "/login",
            data={
                "email": data["email"],
                "password": data["password"],
                "csrf_token": "test-token",
            },
        )
        self.assertEqual(result.status_code, 302)
        self.assertIn("/account", result.location)

    def test_csrf_rejected(self):
        result = self.client.post("/api/reservations", json=self.booking_data())
        self.assertEqual(result.status_code, 403)

    def test_create_and_conflict(self):
        one = self.post("/api/reservations", json=self.booking_data())
        self.assertEqual(one.status_code, 200, one.get_data(as_text=True))
        self.assertTrue(one.json["success"])
        two = self.post("/api/reservations", json=self.booking_data())
        self.assertEqual(two.status_code, 409)

    def test_account_cancellation(self):
        self.post(
            "/register",
            data={
                "name": "Test Guest",
                "phone": "+77071234567",
                "email": "cancel@example.com",
                "password": "Pass12345!",
                "password2": "Pass12345!",
                "csrf_token": "test-token",
            },
        )
        created = self.post("/api/reservations", json=self.booking_data())
        self.assertEqual(created.status_code, 200)
        rid = created.json["reservation_id"]
        cancelled = self.post(
            f"/account/reservations/{rid}/cancel", data={"csrf_token": "test-token"}
        )
        self.assertEqual(cancelled.status_code, 302)
        with closing(sqlite3.connect(self.database)) as conn:
            status = conn.execute(
                "SELECT status FROM reservations WHERE id=?", (rid,)
            ).fetchone()[0]
        self.assertEqual(status, "cancelled")

    def test_admin_authorization_and_tables(self):
        self.assertNotEqual(self.client.get("/api/admin/tables").status_code, 200)
        login = self.post(
            "/admin/login",
            data={
                "username": project.ADMIN_USERNAME,
                "password": project.ADMIN_PASSWORD,
                "csrf_token": "test-token",
            },
        )
        self.assertEqual(login.status_code, 302)
        tables = self.client.get("/api/admin/tables")
        self.assertEqual(tables.status_code, 200)
        self.assertEqual(len(tables.json["tables"]), 16)

    def login_for_payment(self):
        self.post(
            "/register",
            data={
                "name": "Test Guest",
                "phone": "+77071234567",
                "email": "pay@example.com",
                "password": "Pass12345!",
                "password2": "Pass12345!",
            },
        )

    def test_deposit_only_for_large_party_or_preorder(self):
        self.login_for_payment()
        booking = self.post("/api/reservations", json=self.booking_data())
        self.assertEqual(booking.status_code, 200)
        rid = booking.json["reservation_id"]
        account = self.client.get("/account").get_data(as_text=True)
        self.assertNotIn(f"/payment/{rid}", account)
        self.assertEqual(self.client.get(f"/payment/{rid}").status_code, 302)

        large = self.booking_data()
        large["guests"] = 5
        large["table_number"] = 4
        large["reservation_time"] = "20:00"
        created = self.post("/api/reservations", json=large)
        self.assertEqual(created.status_code, 200, created.get_data(as_text=True))
        large_id = created.json["reservation_id"]
        self.assertEqual(self.client.get(f"/payment/{large_id}").status_code, 200)
        account = self.client.get("/account").get_data(as_text=True)
        self.assertIn(f"/payment/{large_id}", account)

        failed = self.post(f"/payment/{large_id}", data={"payment_method": "card"})
        self.assertEqual(failed.status_code, 200)
        self.assertIn("тестовую карту", failed.get_data(as_text=True))
        success = self.post(
            f"/payment/{large_id}",
            data={"payment_method": "card", "demo_card_confirmed": "yes"},
        )
        self.assertEqual(success.status_code, 302)
        self.assertIn("/success", success.location)
        receipt = self.client.get(success.location).get_data(as_text=True)
        self.assertIn("ЭЛЕКТРОННЫЙ ЧЕК", receipt)
        self.assertIn("Столик", receipt)

    def test_deposit_required_for_preorder(self):
        self.login_for_payment()
        menu = self.client.get("/api/menu").json["menu"]
        item = menu[0]
        data = self.booking_data()
        data["preorder"] = [{"menu_item_id": item["id"], "quantity": 1}]
        created = self.post("/api/reservations", json=data)
        self.assertEqual(created.status_code, 200, created.get_data(as_text=True))
        rid = created.json["reservation_id"]
        self.assertEqual(self.client.get(f"/payment/{rid}").status_code, 200)

    def test_small_party_at_large_table_requires_payment(self):
        data = self.booking_data()
        data["table_number"] = 2  # 4 seats for 2 guests
        result = self.post("/api/reservations", json=data)
        self.assertEqual(result.status_code, 200, result.get_data(as_text=True))
        self.assertTrue(result.json["payment_required"])
        rid = result.json["reservation_id"]
        with closing(sqlite3.connect(self.database)) as conn:
            self.assertEqual(
                conn.execute(
                    "SELECT status FROM reservations WHERE id=?", (rid,)
                ).fetchone()[0],
                "pending_payment",
            )
        self.assertEqual(self.client.get(result.json["payment_url"]).status_code, 200)
        paid = self.post(
            result.json["payment_url"],
            data={"payment_method": "card", "demo_card_confirmed": "yes"},
        )
        self.assertEqual(paid.status_code, 302)
        with closing(sqlite3.connect(self.database)) as conn:
            self.assertEqual(
                conn.execute(
                    "SELECT status FROM reservations WHERE id=?", (rid,)
                ).fetchone()[0],
                "confirmed",
            )
        self.assertEqual(self.client.get(paid.location).status_code, 200)

    def test_four_guests_at_six_seats_requires_payment(self):
        data = self.booking_data()
        data.update(table_number=4, guests=4)
        result = self.post("/api/reservations", json=data)
        self.assertTrue(result.json["payment_required"])
        self.assertEqual(
            result.json["payment_url"], "/payment/" + str(result.json["reservation_id"])
        )

    def test_two_guests_at_two_seats_no_payment(self):
        result = self.post("/api/reservations", json=self.booking_data())
        self.assertFalse(result.json["payment_required"])
        self.assertIsNone(result.json["payment_url"])
        with closing(sqlite3.connect(self.database)) as conn:
            self.assertEqual(
                conn.execute(
                    "SELECT status FROM reservations WHERE id=?",
                    (result.json["reservation_id"],),
                ).fetchone()[0],
                "confirmed",
            )

    def test_assistant_books_available_table(self):
        data = self.booking_data()
        data.pop("table_number")
        response = self.post("/api/assistant/book", json=data)
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertTrue(response.json["success"])
        with closing(sqlite3.connect(self.database)) as conn:
            row = conn.execute(
                "SELECT table_number, status FROM reservations WHERE id=?",
                (response.json["reservation_id"],),
            ).fetchone()
        self.assertEqual(row[0], 1)
        self.assertEqual(row[1], "confirmed")

    def test_pending_booking_blocks_double_booking(self):
        data = self.booking_data()
        data.update(table_number=4, guests=5)
        first = self.post("/api/reservations", json=data)
        self.assertTrue(first.json["payment_required"])
        second = self.post("/api/reservations", json=data)
        self.assertEqual(second.status_code, 409)

    def test_assistant_and_menu(self):
        menu = self.client.get("/api/menu")
        self.assertEqual(menu.status_code, 200)
        self.assertGreater(len(menu.json["menu"]), 0)
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            answer = self.post(
                "/api/assistant", json={"message": "Как забронировать стол?"}
            )
        self.assertEqual(answer.status_code, 200)
        self.assertTrue(answer.json["answer"])
        self.assertEqual(answer.json["mode"], "faq")


if __name__ == "__main__":
    unittest.main()
