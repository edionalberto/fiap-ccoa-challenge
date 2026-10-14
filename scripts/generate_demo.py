from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path
import random
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("America/Sao_Paulo")
SEED = 570560


def build_demo() -> dict:
    rng = random.Random(SEED)
    units = [
        {"id": "unit-101", "number": "101"},
        {"id": "unit-202", "number": "202"},
        {"id": "unit-303", "number": "303"},
    ]
    users = [
        {"id": "user-ana", "name": "Ana (demonstração)", "unit_id": "unit-101", "active": True},
        {"id": "user-bruno", "name": "Bruno (demonstração)", "unit_id": "unit-101", "active": True},
        {"id": "user-caio", "name": "Caio (demonstração)", "unit_id": "unit-202", "active": True},
        {"id": "user-diana", "name": "Diana (demonstração)", "unit_id": "unit-303", "active": True},
    ]
    vehicles = [
        {"id": "vehicle-101-a", "unit_id": "unit-101", "label": "Veículo A — unidade 101"},
        {"id": "vehicle-101-b", "unit_id": "unit-101", "label": "Veículo B — unidade 101"},
        {"id": "vehicle-202-a", "unit_id": "unit-202", "label": "Veículo A — unidade 202"},
        {"id": "vehicle-303-a", "unit_id": "unit-303", "label": "Veículo A — unidade 303"},
    ]
    rfid_cards = [
        {"token": "DEMO-RFID-101-A", "user_id": "user-ana", "active": True},
        {"token": "DEMO-RFID-101-B", "user_id": "user-bruno", "active": True},
        {"token": "DEMO-RFID-202-A", "user_id": "user-caio", "active": True},
        {"token": "DEMO-RFID-303-A", "user_id": "user-diana", "active": True},
        {"token": "DEMO-RFID-INACTIVE", "user_id": "user-diana", "active": False},
    ]
    chargers = [
        {"id": "hca-g2-01", "name": "HCA G2 01 (simulado)", "operational": True},
        {"id": "hca-g2-02", "name": "HCA G2 02 (simulado)", "operational": True},
    ]
    user_vehicle = {
        "user-ana": ("unit-101", "vehicle-101-a"),
        "user-bruno": ("unit-101", "vehicle-101-b"),
        "user-caio": ("unit-202", "vehicle-202-a"),
        "user-diana": ("unit-303", "vehicle-303-a"),
    }
    owners = ["user-ana", "user-bruno", "user-caio", "user-diana"]
    meters = {"hca-g2-01": Decimal("100.000"), "hca-g2-02": Decimal("200.000")}
    sessions = []
    start_day = date(2026, 7, 20)
    for day_index in range(56):
        current_day = start_day + timedelta(days=day_index)
        windows = [
            ("hca-g2-01", rng.choice([6, 7, 8]), rng.choice([1, 2])),
            ("hca-g2-02", rng.choice([10, 11, 12]), rng.choice([1, 2])),
            ("hca-g2-01", rng.choice([16, 17, 18]), rng.choice([1, 2])),
        ]
        for window_index, (charger_id, start_hour, duration) in enumerate(windows):
            user_id = owners[(day_index + window_index) % len(owners)]
            unit_id, vehicle_id = user_vehicle[user_id]
            started = datetime(current_day.year, current_day.month, current_day.day, start_hour, tzinfo=TZ)
            ended = started + timedelta(hours=duration)
            measurements = []
            energy_sum = Decimal("0")
            for hour_offset in range(duration):
                bucket_hour = start_hour + hour_offset
                if 6 <= bucket_hour < 9 or 16 <= bucket_hour < 20:
                    low, high = 5, 10
                else:
                    low, high = 3, 7
                if current_day.weekday() >= 5:
                    high = max(low, high - 1)
                energy = Decimal(rng.randint(low, high)).quantize(Decimal("0.001"))
                interval_start = started + timedelta(hours=hour_offset)
                interval_end = interval_start + timedelta(hours=1)
                session_id = f"DEMO-{current_day:%Y%m%d}-{window_index + 1:02d}"
                measurements.append({
                    "session_id": session_id,
                    "charger_id": charger_id,
                    "interval_start": interval_start.isoformat(timespec="seconds"),
                    "interval_end": interval_end.isoformat(timespec="seconds"),
                    "energy_kwh": f"{energy:.3f}",
                    "source": "synthetic",
                })
                energy_sum += energy
            meter_start = meters[charger_id]
            meter_end = meter_start + energy_sum
            meters[charger_id] = meter_end
            sessions.append({
                "id": session_id,
                "source_event_id": session_id,
                "user_id": user_id,
                "unit_id": unit_id,
                "vehicle_id": vehicle_id,
                "charger_id": charger_id,
                "started_at": started.isoformat(timespec="seconds"),
                "ended_at": ended.isoformat(timespec="seconds"),
                "meter_start_kwh": f"{meter_start:.3f}",
                "meter_end_kwh": f"{meter_end:.3f}",
                "tariff_brl_per_kwh": "1.00",
                "status": "CLOSED",
                "measurements": measurements,
            })
    return {
        "schema_version": 1,
        "description": "Dados sintéticos determinísticos; não representam equipamento GoodWe nem consumo real.",
        "tariff_brl_per_kwh": "1.00",
        "units": units,
        "users": users,
        "vehicles": vehicles,
        "rfid_cards": rfid_cards,
        "chargers": chargers,
        "sessions": sessions,
    }


def main() -> None:
    target = ROOT / "data" / "demo.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(build_demo(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Dados de demonstração determinísticos gravados em {target}")


if __name__ == "__main__":
    main()
