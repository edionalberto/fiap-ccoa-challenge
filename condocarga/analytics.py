from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from math import cos, pi, sin
from zoneinfo import ZoneInfo

from sklearn.linear_model import LinearRegression

from .database import connect
from .domain import parse_aware_datetime
from .settings import TIMEZONE

MIN_HISTORY_HOURS = 24 * 14


def hourly_series(db_path=None) -> list[dict]:
    conn = connect(db_path)
    try:
        rows = conn.execute("SELECT interval_start, energy_kwh FROM hourly_measurements WHERE source='synthetic' ORDER BY interval_start").fetchall()
    finally:
        conn.close()
    if not rows:
        return []
    zone = ZoneInfo(TIMEZONE)
    values: dict[datetime, float] = defaultdict(float)
    for row in rows:
        instant = parse_aware_datetime(row["interval_start"], "Início da medição").astimezone(zone)
        bucket = instant.replace(minute=0, second=0, microsecond=0)
        values[bucket] += float(row["energy_kwh"])
    first, last = min(values), max(values)
    series = []
    cursor = first
    while cursor <= last:
        series.append({"timestamp": cursor, "energy_kwh": values.get(cursor, 0.0)})
        cursor += timedelta(hours=1)
    return series


def _features(moment: datetime) -> list[float]:
    hour_angle = 2 * pi * moment.hour / 24
    weekday_angle = 2 * pi * moment.weekday() / 7
    return [sin(hour_angle), cos(hour_angle), sin(weekday_angle), cos(weekday_angle), float(moment.weekday() >= 5)]


def _baseline_map(training: list[dict]) -> dict[int, float]:
    buckets: dict[int, list[float]] = defaultdict(list)
    for sample in training:
        stamp = sample["timestamp"]
        buckets[stamp.weekday() * 24 + stamp.hour].append(sample["energy_kwh"])
    return {key: sum(values) / len(values) for key, values in buckets.items()}


def _baseline_predict(moment: datetime, baseline: dict[int, float], overall: float) -> float:
    key = moment.weekday() * 24 + moment.hour
    return max(0.0, baseline.get(key, overall))


def evaluate_forecast(db_path=None) -> dict:
    series = hourly_series(db_path)
    if len(series) < MIN_HISTORY_HOURS:
        return {"enough_history": False, "message": "O histórico sintético ainda não cobre duas semanas completas.", "samples": len(series)}
    split_index = int(len(series) * 0.75)
    training, testing = series[:split_index], series[split_index:]
    if len(training) < 24 * 7 or len(testing) < 24 * 3:
        return {"enough_history": False, "message": "Não há períodos suficientes para uma comparação temporal estável.", "samples": len(series)}
    model = LinearRegression()
    model.fit([_features(item["timestamp"]) for item in training], [item["energy_kwh"] for item in training])
    baseline = _baseline_map(training)
    overall = sum(item["energy_kwh"] for item in training) / len(training)
    model_errors = []
    baseline_errors = []
    for sample in testing:
        actual = sample["energy_kwh"]
        predicted = max(0.0, float(model.predict([_features(sample["timestamp"])])[0]))
        reference = _baseline_predict(sample["timestamp"], baseline, overall)
        model_errors.append(abs(actual - predicted))
        baseline_errors.append(abs(actual - reference))
    model_mae = sum(model_errors) / len(model_errors)
    baseline_mae = sum(baseline_errors) / len(baseline_errors)
    selected = "regressão" if model_mae < baseline_mae else "referência histórica"
    return {
        "enough_history": True,
        "samples": len(series),
        "training_samples": len(training),
        "testing_samples": len(testing),
        "model_mae": model_mae,
        "baseline_mae": baseline_mae,
        "selected_method": selected,
        "model": model,
        "baseline": baseline,
        "overall_mean": overall,
    }


def recommend_hours(preferred_weekdays: list[int], preferred_hours: list[int], limit: int = 8, db_path=None) -> dict:
    evaluation = evaluate_forecast(db_path)
    if not evaluation["enough_history"]:
        return {"available": False, "message": evaluation["message"], "options": []}
    if not preferred_weekdays or not preferred_hours:
        return {"available": False, "message": "Escolha ao menos um dia da semana e uma hora de preferência.", "options": []}
    zone = ZoneInfo(TIMEZONE)
    now = datetime.now(zone).replace(minute=0, second=0, microsecond=0)
    first_candidate = now + timedelta(hours=1)
    candidates = []
    for offset in range(7 * 24):
        moment = first_candidate + timedelta(hours=offset)
        if moment.weekday() not in preferred_weekdays or moment.hour not in preferred_hours:
            continue
        if evaluation["selected_method"] == "regressão":
            demand = max(0.0, float(evaluation["model"].predict([_features(moment)])[0]))
        else:
            demand = _baseline_predict(moment, evaluation["baseline"], evaluation["overall_mean"])
        weekday_names = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
        candidates.append({"Faixa futura": f"{weekday_names[moment.weekday()]} {moment:%d/%m}, {moment.hour:02d}:00",
                           "Demanda estimada (kWh)": round(demand, 2), "method": evaluation["selected_method"]})
    candidates.sort(key=lambda row: (row["Demanda estimada (kWh)"], row["Faixa futura"]))
    if not candidates:
        return {"available": False, "message": "Não há faixas futuras dentro dessas preferências nos próximos sete dias.",
                "evaluation": evaluation, "options": []}
    return {"available": True, "message": "Estimativa orientativa; não consulta disponibilidade e não reserva o carregador.",
            "evaluation": evaluation, "options": candidates[:max(1, limit)]}


