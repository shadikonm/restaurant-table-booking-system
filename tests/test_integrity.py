"""Regression coverage for payment invariants and concurrent SQLite writers."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import unittest
import test_app as base


class IntegrityTests(unittest.TestCase):
    setUp = base.RestaurantTests.setUp
    tearDown = base.RestaurantTests.tearDown
    post = base.RestaurantTests.post
    booking_data = base.RestaurantTests.booking_data
    login_for_payment = base.RestaurantTests.login_for_payment

    def test_admin_cannot_confirm_unpaid(self):
        data = self.booking_data()
        data.update(guests=5, table_number=4)
        rid = self.post("/api/reservations", json=data).json["reservation_id"]
        import app as project

        self.post(
            "/admin/login",
            data={
                "username": project.ADMIN_USERNAME,
                "password": project.ADMIN_PASSWORD,
            },
        )
        with self.client.session_transaction() as session:
            token = session["_csrf_token"]
        response = self.client.patch(
            f"/api/reservations/{rid}/status",
            json={"status": "confirmed"},
            headers={"X-CSRF-Token": token},
        )
        self.assertEqual(response.status_code, 409)
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT status FROM reservations WHERE id=?", (rid,)
                ).fetchone()[0],
                "pending_payment",
            )

    def test_concurrent_writers_only_one_booking(self):
        barrier = Barrier(2)

        def create():
            with sqlite3.connect(self.database, timeout=10) as connection:
                barrier.wait(timeout=10)
                try:
                    connection.execute(
                        """INSERT INTO reservations
                        (table_number, customer_name, phone, guests,
                        reservation_date, reservation_time, status)
                        VALUES (1, 'Concurrency Test', '+77071234567', 2, ?, '18:00', 'confirmed')""",
                        (self.date,),
                    )
                    connection.commit()
                    return "created"
                except sqlite3.IntegrityError as error:
                    self.assertIn("reservation_conflict", str(error))
                    return "conflict"

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: create(), range(2)))
        self.assertCountEqual(results, ["created", "conflict"])

    def test_pending_cancellation(self):
        self.login_for_payment()
        data = self.booking_data()
        data.update(guests=5, table_number=4)
        rid = self.post("/api/reservations", json=data).json["reservation_id"]
        self.assertEqual(
            self.post(f"/account/reservations/{rid}/cancel").status_code, 302
        )
