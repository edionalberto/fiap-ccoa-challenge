from __future__ import annotations

import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from condocarga.analytics import evaluate_forecast, recommend_hours
from condocarga.database import connect
from condocarga.domain import DomainError, quote_session
from condocarga.services import (
    DataError,
    active_sessions,
    cancel_queue_request,
    close_session,
    create_queue_request,
    load_demo_data,
    monthly_report,
    queue_for_charger,
    report_csv,
    start_session,
)

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "data" / "demo.json"
CARD_BY_USER = {"user-ana": "DEMO-RFID-101-A", "user-bruno": "DEMO-RFID-101-B"}
VEHICLE_BY_USER = {"user-ana": "vehicle-101-a", "user-bruno": "vehicle-101-b"}


class CondoCargaWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.db = Path(self.temp.name) / "test.sqlite3"
        self.seed = load_demo_data(DEMO, self.db)

    def tearDown(self):
        self.temp.cleanup()

    def test_demo_seed_is_idempotent_and_hourly_energy_reconciles(self):
        load_demo_data(DEMO, self.db)
        conn = connect(self.db)
        try:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0], 168)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM units").fetchone()[0], 3)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0], 4)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM hourly_measurements").fetchone()[0], self.seed["measurements"])
        finally:
            conn.close()

    def test_invalid_hourly_seed_is_rejected_before_persistence(self):
        document = json.loads(DEMO.read_text(encoding="utf-8"))
        document["sessions"][0]["measurements"][0]["energy_kwh"] = "999.000"
        invalid_file = Path(self.temp.name) / "invalid.json"
        invalid_file.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(DataError):
            load_demo_data(invalid_file, Path(self.temp.name) / "invalid.sqlite3")

    def test_round_half_up_and_zero_use(self):
        self.assertEqual(quote_session("0", "1.005", "1").amount_cents, 101)
        zero_report = monthly_report(2026, 10, self.db)
        self.assertEqual(zero_report["amount_cents"], 0)
        self.assertTrue(any(unit["unit_number"] == "303" and unit["amount_cents"] == 0 for unit in zero_report["units"]))

    def test_monthly_report_includes_session_detail_and_csv_totals(self):
        report = monthly_report(2026, 7, self.db)
        self.assertGreater(report["amount_cents"], 0)
        self.assertEqual(sum(unit["amount_cents"] for unit in report["units"]), report["amount_cents"])
        self.assertIn("total_periodo", report_csv(report))

    def test_invalid_close_keeps_session_active_and_charger_occupied(self):
        session_id = start_session(CARD_BY_USER["user-ana"], "hca-g2-01", "5000.000", VEHICLE_BY_USER["user-ana"],
                                   "2026-09-20T10:00:00-03:00", db_path=self.db)
        with self.assertRaises(DomainError):
            close_session(session_id, "4999.000", "2026-09-20T11:00:00-03:00", self.db)
        self.assertEqual(active_sessions("hca-g2-01", self.db)[0]["id"], session_id)
        quote = close_session(session_id, "5002.500", "2026-09-20T11:00:00-03:00", self.db)
        self.assertEqual(quote["amount_cents"], 250)

    def test_queue_tie_break_bypass_cancel_and_served_state(self):
        created = "2026-09-20T10:00:00-03:00"
        a = create_queue_request("user-ana", "hca-g2-02", created, self.db)
        b = create_queue_request("user-bruno", "hca-g2-02", created, self.db)
        queue = queue_for_charger("hca-g2-02", self.db)
        self.assertEqual([row["request_id"] for row in queue], sorted([a, b]))
        head, tail = queue
        with self.assertRaises(DomainError):
            start_session(CARD_BY_USER[tail["user_id"]], "hca-g2-02", "7000.000", VEHICLE_BY_USER[tail["user_id"]],
                          "2026-09-20T10:00:00-03:00", tail["request_id"], self.db)
        cancel_queue_request(head["request_id"], head["user_id"], self.db)
        next_request = queue_for_charger("hca-g2-02", self.db)[0]
        session_id = start_session(CARD_BY_USER[next_request["user_id"]], "hca-g2-02", "7000.000",
                                   VEHICLE_BY_USER[next_request["user_id"]], "2026-09-20T10:00:00-03:00",
                                   next_request["request_id"], self.db)
        conn = connect(self.db)
        try:
            status = conn.execute("SELECT status FROM queue_requests WHERE request_id=?", (next_request["request_id"],)).fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(status, "SERVED")
        self.assertEqual(active_sessions("hca-g2-02", self.db)[0]["id"], session_id)

    def test_inactive_card_cannot_start(self):
        with self.assertRaises(DomainError):
            start_session("DEMO-RFID-INACTIVE", "hca-g2-02", "7000.000", "vehicle-303-a",
                          "2026-09-20T10:00:00-03:00", db_path=self.db)

    def test_forecast_uses_temporal_holdout_and_recommendations_are_advisory(self):
        result = evaluate_forecast(self.db)
        self.assertTrue(result["enough_history"])
        self.assertLess(result["training_samples"], result["samples"])
        self.assertGreater(result["testing_samples"], 0)
        self.assertIn(result["selected_method"], {"regressão", "referência histórica"})
        recommendation = recommend_hours(list(range(7)), list(range(24)), db_path=self.db)
        self.assertTrue(recommendation["available"])
        self.assertGreater(len(recommendation["options"]), 0)
        self.assertIn("não reserva", recommendation["message"])


    def test_session_crossing_month_is_billed_in_end_month(self):
        session_id = start_session(CARD_BY_USER["user-ana"], "hca-g2-02", "8000.000", VEHICLE_BY_USER["user-ana"],
                                   "2026-07-31T23:00:00-03:00", db_path=self.db)
        close_session(session_id, "8003.000", "2026-08-01T00:00:00-03:00", self.db)
        july = monthly_report(2026, 7, self.db)
        august = monthly_report(2026, 8, self.db)
        self.assertNotIn(session_id, [item["id"] for unit in july["units"] for item in unit["sessions"]])
        august_rows = [item for unit in august["units"] for item in unit["sessions"]]
        self.assertEqual(next(item for item in august_rows if item["id"] == session_id)["amount_cents"], 300)

    def test_invalid_end_time_leaves_session_active(self):
        session_id = start_session(CARD_BY_USER["user-ana"], "hca-g2-02", "9000.000", VEHICLE_BY_USER["user-ana"],
                                   "2026-09-21T10:00:00-03:00", db_path=self.db)
        with self.assertRaises(DomainError):
            close_session(session_id, "9001.000", "2026-09-21T09:59:00-03:00", self.db)
        self.assertEqual(active_sessions("hca-g2-02", self.db)[0]["id"], session_id)

    def test_tariff_is_captured_when_session_starts(self):
        from condocarga.services import update_tariff
        session_id = start_session(CARD_BY_USER["user-ana"], "hca-g2-02", "10000.000", VEHICLE_BY_USER["user-ana"],
                                   "2026-09-22T10:00:00-03:00", db_path=self.db)
        update_tariff("2.50", self.db)
        quote = close_session(session_id, "10002.000", "2026-09-22T11:00:00-03:00", self.db)
        self.assertEqual(quote["amount_cents"], 200)

if __name__ == "__main__":
    unittest.main()


