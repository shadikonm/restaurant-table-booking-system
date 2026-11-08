"""Database-level invariants shared by creation, editing and status changes."""


def install_invariants(connection):
    for event, name, exclusion in (
        ("INSERT", "reservation_conflict_insert", ""),
        ("UPDATE", "reservation_conflict_update", "AND r.id != NEW.id"),
    ):
        connection.execute(f"""CREATE TRIGGER IF NOT EXISTS {name}
            BEFORE {event} ON reservations
            WHEN NEW.status IN ('confirmed', 'arrived', 'pending_payment')
            AND EXISTS (
                SELECT 1 FROM reservations r
                WHERE r.table_number = NEW.table_number
                AND r.status IN ('confirmed', 'arrived', 'pending_payment')
                {exclusion}
                AND julianday(r.reservation_date || ' ' || r.reservation_time)
                    < julianday(NEW.reservation_date || ' ' || NEW.reservation_time, '+2 hours')
                AND julianday(NEW.reservation_date || ' ' || NEW.reservation_time)
                    < julianday(r.reservation_date || ' ' || r.reservation_time, '+2 hours')
            ) BEGIN SELECT RAISE(ABORT, 'reservation_conflict'); END""")
    connection.execute("""CREATE TRIGGER IF NOT EXISTS reservation_payment_guard
        BEFORE UPDATE ON reservations
        WHEN NEW.status IN ('confirmed', 'arrived', 'completed')
        AND NEW.payment_status != 'paid'
        AND (NEW.guests > 4
            OR EXISTS (SELECT 1 FROM reservation_items WHERE reservation_id = NEW.id)
            OR (NEW.guests = 4 AND (SELECT capacity FROM table_settings WHERE table_number = NEW.table_number) = 6)
            OR (NEW.guests IN (1, 2) AND (SELECT capacity FROM table_settings WHERE table_number = NEW.table_number) > 2))
        BEGIN SELECT RAISE(ABORT, 'payment_required'); END""")
