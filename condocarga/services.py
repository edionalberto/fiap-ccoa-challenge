from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from .database import connect, initialize_database, transaction
from .domain import DomainError, local_month, local_now, parse_aware_datetime, parse_decimal, quote_session
from .settings import DB_PATH, DEFAULT_TARIFF, DEMO_PATH, TIMEZONE


class DataError(ValueError):
    """Seed data violates the documented internal contract."""


def _validate_demo(document: dict) -> None:
    units = {row["id"] for row in document.get("units", [])}
    users = {row["id"] for row in document.get("users", [])}
    vehicles = {row["id"] for row in document.get("vehicles", [])}
    chargers = {row["id"] for row in document.get("chargers", [])}
    card_tokens = {row["token"] for row in document.get("rfid_cards", [])}
    if len(units) != len(document.get("units", [])):
        raise DataError("A carga contém unidades duplicadas.")
    if len(users) != len(document.get("users", [])) or len(chargers) != len(document.get("chargers", [])):
        raise DataError("A carga contém IDs de usuário ou carregador duplicados.")
    if len(card_tokens) != len(document.get("rfid_cards", [])):
        raise DataError("A carga contém cartões duplicados.")
    for user in document.get("users", []):
        if user["unit_id"] not in units:
            raise DataError(f"Usuário {user['id']} aponta para uma unidade inexistente.")
    for vehicle in document.get("vehicles", []):
        if vehicle["unit_id"] not in units:
            raise DataError(f"Veículo {vehicle['id']} aponta para uma unidade inexistente.")
    for card in document.get("rfid_cards", []):
        if card["user_id"] not in users:
            raise DataError(f"Cartão de {card['user_id']} aponta para um usuário inexistente.")

    seen_sessions: set[str] = set()
    seen_intervals: dict[str, list[tuple[datetime, datetime, str]]] = defaultdict(list)
    for session in document.get("sessions", []):
        sid = session["id"]
        if sid in seen_sessions:
            raise DataError(f"Sessão duplicada na carga: {sid}.")
        seen_sessions.add(sid)
        if session["user_id"] not in users or session["unit_id"] not in units or session["charger_id"] not in chargers:
            raise DataError(f"Sessão {sid} referencia cadastro inexistente.")
        if session.get("vehicle_id") and session["vehicle_id"] not in vehicles:
            raise DataError(f"Sessão {sid} referencia veículo inexistente.")
        if session.get("status") != "CLOSED":
            raise DataError(f"A carga demonstrativa aceita apenas sessões encerradas: {sid}.")
        start = parse_aware_datetime(session["started_at"], "Início da sessão")
        end = parse_aware_datetime(session["ended_at"], "Fim da sessão")
        if end < start:
            raise DataError(f"Horário final anterior ao início na sessão {sid}.")
        quote = quote_session(session["meter_start_kwh"], session["meter_end_kwh"], session["tariff_brl_per_kwh"])
        if start.minute or start.second or end.minute or end.second or (end - start) % timedelta(hours=1):
            raise DataError(f"A sessão demonstrativa {sid} deve usar horas completas.")
        measurements = session.get("measurements", [])
        total = Decimal("0")
        cursor = start
        if quote.energy_kwh > 0 and not measurements:
            raise DataError(f"Sessão {sid} precisa de medições horárias sintéticas conciliáveis.")
        for measurement in measurements:
            m_start = parse_aware_datetime(measurement["interval_start"], "Início da medição")
            m_end = parse_aware_datetime(measurement["interval_end"], "Fim da medição")
            value = parse_decimal(measurement["energy_kwh"], "Energia horária")
            if measurement.get("session_id") != sid or measurement.get("charger_id") != session["charger_id"]:
                raise DataError(f"Medição não vinculada à sessão/carregador em {sid}.")
            if measurement.get("source") != "synthetic":
                raise DataError("A carga MVP deve identificar medições como synthetic.")
            if m_start.tzinfo is None or m_end.tzinfo is None or m_start.minute or m_start.second or m_end - m_start != timedelta(hours=1):
                raise DataError(f"Intervalo horário inválido em {sid}.")
            local_start = m_start.astimezone(ZoneInfo(TIMEZONE))
            if local_start.minute or local_start.second or m_start != cursor:
                raise DataError(f"Intervalos horários incompletos ou fora de ordem em {sid}.")
            if value < 0:
                raise DataError(f"Energia negativa em {sid}.")
            cursor = m_end
            total += value
            seen_intervals[session["charger_id"]].append((m_start, m_end, sid))
        if measurements and cursor != end:
            raise DataError(f"Medições não cobrem toda a sessão {sid}.")
        if total != quote.energy_kwh:
            raise DataError(f"Medições da sessão {sid} somam {total}, mas a sessão mede {quote.energy_kwh} kWh.")
    for charger_id, intervals in seen_intervals.items():
        intervals.sort(key=lambda item: item[0])
        for previous, current in zip(intervals, intervals[1:]):
            if current[0] < previous[1]:
                raise DataError(f"Medições sobrepostas no carregador {charger_id}.")


def load_demo_data(path: Path | str = DEMO_PATH, db_path: Path | str | None = None) -> dict[str, int]:
    with Path(path).open("r", encoding="utf-8") as handle:
        document = json.load(handle)
    _validate_demo(document)
    initialize_database(db_path)
    with transaction(db_path) as conn:
        for unit in document["units"]:
            conn.execute("INSERT OR IGNORE INTO units(id, number) VALUES (?, ?)", (unit["id"], unit["number"]))
        for user in document["users"]:
            conn.execute("INSERT OR IGNORE INTO users(id, name, unit_id, active) VALUES (?, ?, ?, ?)",
                         (user["id"], user["name"], user["unit_id"], int(user.get("active", True))))
        for vehicle in document["vehicles"]:
            conn.execute("INSERT OR IGNORE INTO vehicles(id, unit_id, label) VALUES (?, ?, ?)",
                         (vehicle["id"], vehicle["unit_id"], vehicle["label"]))
        for card in document["rfid_cards"]:
            conn.execute("INSERT OR IGNORE INTO rfid_cards(token, user_id, active) VALUES (?, ?, ?)",
                         (card["token"], card["user_id"], int(card.get("active", True))))
        for charger in document["chargers"]:
            conn.execute("INSERT OR IGNORE INTO chargers(id, name, operational) VALUES (?, ?, ?)",
                         (charger["id"], charger["name"], int(charger.get("operational", True))))
        conn.execute("INSERT OR IGNORE INTO tariff_config(id, brl_per_kwh, updated_at) VALUES (1, ?, ?)",
                     (document.get("tariff_brl_per_kwh", DEFAULT_TARIFF), local_now().isoformat()))
        for session in document["sessions"]:
            conn.execute("""INSERT OR IGNORE INTO sessions
                (id, source_event_id, user_id, unit_id, vehicle_id, charger_id, started_at, ended_at,
                 meter_start_kwh, meter_end_kwh, tariff_brl_per_kwh, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'CLOSED')""",
                         (session["id"], session.get("source_event_id", session["id"]), session["user_id"],
                          session["unit_id"], session.get("vehicle_id"), session["charger_id"], session["started_at"],
                          session["ended_at"], str(session["meter_start_kwh"]), str(session["meter_end_kwh"]),
                          str(session["tariff_brl_per_kwh"])))
            for index, measurement in enumerate(session.get("measurements", []), start=1):
                conn.execute("""INSERT OR IGNORE INTO hourly_measurements
                    (id, session_id, charger_id, interval_start, interval_end, energy_kwh, source)
                    VALUES (?, ?, ?, ?, ?, ?, 'synthetic')""",
                             (f"{session['id']}-H{index:02d}", session["id"], session["charger_id"],
                              measurement["interval_start"], measurement["interval_end"], str(measurement["energy_kwh"])))
        return {
            "units": len(document["units"]),
            "users": len(document["users"]),
            "sessions": len(document["sessions"]),
            "measurements": sum(len(row.get("measurements", [])) for row in document["sessions"]),
        }


def database_is_seeded(db_path: Path | str | None = None) -> bool:
    initialize_database(db_path)
    conn = connect(db_path)
    try:
        return conn.execute("SELECT EXISTS(SELECT 1 FROM sessions)").fetchone()[0] == 1
    finally:
        conn.close()


def list_units(db_path=None) -> list[dict]:
    conn = connect(db_path)
    try:
        return [dict(row) for row in conn.execute("SELECT id, number FROM units ORDER BY number")]
    finally:
        conn.close()


def list_users(db_path=None, unit_id: str | None = None) -> list[dict]:
    conn = connect(db_path)
    try:
        query = "SELECT u.id, u.name, u.unit_id, un.number AS unit_number FROM users u JOIN units un ON un.id=u.unit_id WHERE u.active=1"
        args: tuple = ()
        if unit_id:
            query += " AND u.unit_id=?"
            args = (unit_id,)
        query += " ORDER BY un.number, u.name"
        return [dict(row) for row in conn.execute(query, args)]
    finally:
        conn.close()


def list_vehicles(unit_id: str, db_path=None) -> list[dict]:
    conn = connect(db_path)
    try:
        return [dict(row) for row in conn.execute("SELECT id, unit_id, label FROM vehicles WHERE unit_id=? ORDER BY label", (unit_id,))]
    finally:
        conn.close()


def list_chargers(db_path=None) -> list[dict]:
    conn = connect(db_path)
    try:
        return [dict(row) for row in conn.execute("SELECT id, name, operational FROM chargers ORDER BY name")]
    finally:
        conn.close()


def current_tariff(db_path=None) -> str:
    conn = connect(db_path)
    try:
        row = conn.execute("SELECT brl_per_kwh FROM tariff_config WHERE id=1").fetchone()
        return row[0] if row else DEFAULT_TARIFF
    finally:
        conn.close()


def update_tariff(value: str | Decimal, db_path=None) -> str:
    amount = parse_decimal(value, "Tarifa")
    if amount < 0 or amount.as_tuple().exponent < -4:
        raise DomainError("A tarifa deve ser não negativa e ter até quatro casas decimais.")
    normalized = format(amount, "f")
    with transaction(db_path) as conn:
        conn.execute("""INSERT INTO tariff_config(id, brl_per_kwh, updated_at) VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET brl_per_kwh=excluded.brl_per_kwh, updated_at=excluded.updated_at""",
                     (normalized, local_now().isoformat()))
    return normalized


def _serialize_datetime(value: str | datetime) -> str:
    return parse_aware_datetime(value, "Data e hora").isoformat(timespec="seconds")


def active_sessions(charger_id: str | None = None, db_path=None) -> list[dict]:
    conn = connect(db_path)
    try:
        sql = """SELECT s.*, u.name AS user_name, un.number AS unit_number, c.name AS charger_name,
                  v.label AS vehicle_label FROM sessions s JOIN users u ON u.id=s.user_id
                  JOIN units un ON un.id=s.unit_id JOIN chargers c ON c.id=s.charger_id
                  LEFT JOIN vehicles v ON v.id=s.vehicle_id WHERE s.status='ACTIVE'"""
        args: tuple = ()
        if charger_id:
            sql += " AND s.charger_id=?"
            args = (charger_id,)
        sql += " ORDER BY s.started_at"
        return [dict(row) for row in conn.execute(sql, args)]
    finally:
        conn.close()


def create_queue_request(user_id: str, charger_id: str, created_at: str | datetime | None = None, db_path=None) -> str:
    request_id = str(uuid4())
    timestamp = _serialize_datetime(created_at or local_now())
    with transaction(db_path) as conn:
        user = conn.execute("SELECT active FROM users WHERE id=?", (user_id,)).fetchone()
        charger = conn.execute("SELECT operational FROM chargers WHERE id=?", (charger_id,)).fetchone()
        if not user or not user[0]:
            raise DomainError("Perfil de morador inativo ou inexistente.")
        if not charger or not charger[0]:
            raise DomainError("Carregador indisponível para novas solicitações.")
        if conn.execute("SELECT 1 FROM sessions WHERE user_id=? AND charger_id=? AND status='ACTIVE'", (user_id, charger_id)).fetchone():
            raise DomainError("Este morador já está usando o carregador.")
        if conn.execute("SELECT 1 FROM queue_requests WHERE user_id=? AND charger_id=? AND status='WAITING'", (user_id, charger_id)).fetchone():
            raise DomainError("Já existe uma solicitação sua em espera para este carregador.")
        conn.execute("INSERT INTO queue_requests(request_id,user_id,charger_id,created_at,status) VALUES(?,?,?,?,'WAITING')",
                     (request_id, user_id, charger_id, timestamp))
    return request_id


def queue_for_charger(charger_id: str, db_path=None) -> list[dict]:
    conn = connect(db_path)
    try:
        return [dict(row) for row in conn.execute("""SELECT q.request_id, q.user_id, q.charger_id, q.created_at,
                    q.status, u.name AS user_name, un.number AS unit_number
                    FROM queue_requests q JOIN users u ON u.id=q.user_id JOIN units un ON un.id=u.unit_id
                    WHERE q.charger_id=? AND q.status='WAITING' ORDER BY q.created_at, q.request_id""", (charger_id,))]
    finally:
        conn.close()


def cancel_queue_request(request_id: str, user_id: str, db_path=None) -> None:
    with transaction(db_path) as conn:
        result = conn.execute("UPDATE queue_requests SET status='CANCELLED' WHERE request_id=? AND user_id=? AND status='WAITING'",
                              (request_id, user_id))
        if result.rowcount != 1:
            raise DomainError("A solicitação não está em espera ou não pertence a este morador.")


def start_session(rfid_token: str, charger_id: str, meter_start_kwh: str | Decimal,
                  vehicle_id: str | None = None, started_at: str | datetime | None = None,
                  request_id: str | None = None, db_path=None) -> str:
    start_value = parse_decimal(meter_start_kwh, "Leitura inicial")
    if start_value < 0:
        raise DomainError("A leitura inicial não pode ser negativa.")
    timestamp = _serialize_datetime(started_at or local_now())
    session_id = str(uuid4())
    with transaction(db_path) as conn:
        card = conn.execute("""SELECT r.user_id, r.active AS card_active, u.unit_id, u.active AS user_active
                            FROM rfid_cards r JOIN users u ON u.id=r.user_id WHERE r.token=?""", (rfid_token,)).fetchone()
        if not card or not card["card_active"] or not card["user_active"]:
            raise DomainError("Credencial RFID desconhecida ou inativa.")
        charger = conn.execute("SELECT operational FROM chargers WHERE id=?", (charger_id,)).fetchone()
        if not charger or not charger[0]:
            raise DomainError("Carregador inexistente ou em manutenção.")
        if conn.execute("SELECT 1 FROM sessions WHERE charger_id=? AND status='ACTIVE'", (charger_id,)).fetchone():
            raise DomainError("O carregador já possui uma sessão ativa.")
        waiting = conn.execute("""SELECT request_id, user_id FROM queue_requests WHERE charger_id=? AND status='WAITING'
                                 ORDER BY created_at, request_id""", (charger_id,)).fetchall()
        if waiting:
            first = waiting[0]
            if not request_id or first["request_id"] != request_id or first["user_id"] != card["user_id"]:
                raise DomainError("Somente o primeiro morador da fila pode iniciar a sessão.")
        elif request_id:
            request = conn.execute("SELECT user_id,status FROM queue_requests WHERE request_id=? AND charger_id=?", (request_id, charger_id)).fetchone()
            if not request or request["status"] != "WAITING" or request["user_id"] != card["user_id"]:
                raise DomainError("Solicitação inválida para iniciar sessão.")
        if vehicle_id:
            vehicle = conn.execute("SELECT unit_id FROM vehicles WHERE id=?", (vehicle_id,)).fetchone()
            if not vehicle or vehicle[0] != card["unit_id"]:
                raise DomainError("O veículo não pertence à unidade do morador.")
        tariff = conn.execute("SELECT brl_per_kwh FROM tariff_config WHERE id=1").fetchone()
        tariff_value = tariff[0] if tariff else DEFAULT_TARIFF
        conn.execute("""INSERT INTO sessions(id,source_event_id,user_id,unit_id,vehicle_id,charger_id,started_at,
                         meter_start_kwh,tariff_brl_per_kwh,status) VALUES(?,?,?,?,?,?,?,?,?,'ACTIVE')""",
                     (session_id, session_id, card["user_id"], card["unit_id"], vehicle_id, charger_id,
                      timestamp, str(start_value), tariff_value))
        if request_id:
            conn.execute("UPDATE queue_requests SET status='SERVED' WHERE request_id=? AND status='WAITING'", (request_id,))
    return session_id


def close_session(session_id: str, meter_end_kwh: str | Decimal, ended_at: str | datetime | None = None, db_path=None) -> dict:
    end_value = parse_decimal(meter_end_kwh, "Leitura final")
    timestamp = _serialize_datetime(ended_at or local_now())
    with transaction(db_path) as conn:
        session = conn.execute("SELECT * FROM sessions WHERE id=? AND status='ACTIVE'", (session_id,)).fetchone()
        if not session:
            raise DomainError("A sessão não está ativa ou não existe.")
        quote = quote_session(session["meter_start_kwh"], end_value, session["tariff_brl_per_kwh"])
        started = parse_aware_datetime(session["started_at"], "Início da sessão")
        ended = parse_aware_datetime(timestamp, "Fim da sessão")
        if ended < started:
            raise DomainError("O horário final não pode anteceder o início. A sessão permanece ativa.")
        conn.execute("UPDATE sessions SET ended_at=?, meter_end_kwh=?, status='CLOSED' WHERE id=? AND status='ACTIVE'",
                     (timestamp, str(end_value), session_id))
    return {"energy_kwh": quote.energy_kwh, "tariff_brl_per_kwh": quote.tariff_brl_per_kwh,
            "amount_brl": quote.amount_brl, "amount_cents": quote.amount_cents}


def resident_sessions(unit_id: str, db_path=None) -> list[dict]:
    conn = connect(db_path)
    try:
        return [dict(row) for row in conn.execute("""SELECT s.*,u.name AS user_name,un.number AS unit_number,
            c.name AS charger_name,v.label AS vehicle_label FROM sessions s
            JOIN users u ON u.id=s.user_id JOIN units un ON un.id=s.unit_id JOIN chargers c ON c.id=s.charger_id
            LEFT JOIN vehicles v ON v.id=s.vehicle_id WHERE s.unit_id=? ORDER BY s.started_at DESC""", (unit_id,))]
    finally:
        conn.close()


def latest_meter(charger_id: str, db_path=None) -> str:
    conn = connect(db_path)
    try:
        active = conn.execute("SELECT meter_start_kwh FROM sessions WHERE charger_id=? AND status='ACTIVE'", (charger_id,)).fetchone()
        if active:
            return active[0]
        row = conn.execute("SELECT meter_end_kwh FROM sessions WHERE charger_id=? AND status='CLOSED' ORDER BY ended_at DESC, id DESC LIMIT 1", (charger_id,)).fetchone()
        return row[0] if row else "0.000"
    finally:
        conn.close()


def monthly_report(year: int, month: int, db_path=None) -> dict:
    conn = connect(db_path)
    try:
        units = [dict(row) for row in conn.execute("SELECT id,number FROM units ORDER BY number")]
        rows = conn.execute("""SELECT s.*, u.name AS user_name, un.number AS unit_number,
            c.name AS charger_name, v.label AS vehicle_label
            FROM sessions s JOIN users u ON u.id=s.user_id JOIN units un ON un.id=s.unit_id
            JOIN chargers c ON c.id=s.charger_id LEFT JOIN vehicles v ON v.id=s.vehicle_id
            WHERE s.status='CLOSED' ORDER BY s.ended_at, un.number, s.id""").fetchall()
    finally:
        conn.close()
    requested_period = f"{year:04d}-{month:02d}"
    totals = {unit["id"]: {"unit_id": unit["id"], "unit_number": unit["number"], "energy_kwh": Decimal("0"), "amount_cents": 0, "sessions": []} for unit in units}
    for row in rows:
        item = dict(row)
        if local_month(item["ended_at"]) != requested_period:
            continue
        quote = quote_session(item["meter_start_kwh"], item["meter_end_kwh"], item["tariff_brl_per_kwh"])
        item.update({"energy_kwh": quote.energy_kwh, "amount_brl": quote.amount_brl,
                     "amount_cents": quote.amount_cents, "month": requested_period})
        bucket = totals[item["unit_id"]]
        bucket["energy_kwh"] += quote.energy_kwh
        bucket["amount_cents"] += quote.amount_cents
        bucket["sessions"].append(item)
    summaries = list(totals.values())
    for summary in summaries:
        summary["amount_brl"] = (Decimal(summary["amount_cents"]) / 100).quantize(Decimal("0.01"))
    return {"period": requested_period, "units": summaries,
            "energy_kwh": sum((row["energy_kwh"] for row in summaries), Decimal("0")),
            "amount_cents": sum(row["amount_cents"] for row in summaries),
            "amount_brl": (Decimal(sum(row["amount_cents"] for row in summaries)) / 100).quantize(Decimal("0.01"))}


def report_csv(report: dict) -> str:
    from io import StringIO
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["tipo", "periodo", "unidade", "sessao", "morador", "veiculo", "carregador",
                     "inicio", "encerramento", "leitura_inicial_kwh", "leitura_final_kwh",
                     "consumo_kwh", "tarifa_brl_kwh", "valor_brl"])
    for unit in report["units"]:
        if not unit["sessions"]:
            writer.writerow(["unidade", report["period"], unit["unit_number"], "", "", "", "", "", "", "", "", "0.000", "", "0.00"])
            continue
        for session in unit["sessions"]:
            writer.writerow(["sessao", report["period"], unit["unit_number"], session["id"], session["user_name"],
                             session["vehicle_label"] or "", session["charger_name"], session["started_at"], session["ended_at"],
                             session["meter_start_kwh"], session["meter_end_kwh"], str(session["energy_kwh"]),
                             session["tariff_brl_per_kwh"], f"{session['amount_brl']:.2f}"])
        writer.writerow(["total_unidade", report["period"], unit["unit_number"], "", "", "", "", "", "", "", "",
                         str(unit["energy_kwh"]), "", f"{unit['amount_brl']:.2f}"])
    writer.writerow(["total_periodo", report["period"], "", "", "", "", "", "", "", "", "",
                     str(report["energy_kwh"]), "", f"{report['amount_brl']:.2f}"])
    return output.getvalue()


def available_report_periods(db_path=None) -> list[str]:
    conn = connect(db_path)
    try:
        rows = conn.execute("SELECT ended_at FROM sessions WHERE status='CLOSED' AND ended_at IS NOT NULL").fetchall()
    finally:
        conn.close()
    periods = {local_month(row[0]) for row in rows}
    periods.add(local_month(local_now()))
    return sorted(periods, reverse=True)


def all_sessions(db_path=None) -> list[dict]:
    conn = connect(db_path)
    try:
        return [dict(row) for row in conn.execute("""SELECT s.*,u.name AS user_name,un.number AS unit_number,
            c.name AS charger_name,v.label AS vehicle_label FROM sessions s JOIN users u ON u.id=s.user_id
            JOIN units un ON un.id=s.unit_id JOIN chargers c ON c.id=s.charger_id
            LEFT JOIN vehicles v ON v.id=s.vehicle_id ORDER BY s.started_at DESC""")]
    finally:
        conn.close()
