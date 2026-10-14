from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from .settings import TIMEZONE

CENT = Decimal("0.01")


class DomainError(ValueError):
    """A business rule prevents the requested operation."""


@dataclass(frozen=True)
class SessionQuote:
    energy_kwh: Decimal
    tariff_brl_per_kwh: Decimal
    amount_brl: Decimal
    amount_cents: int


def parse_decimal(value: str | int | float | Decimal, label: str) -> Decimal:
    try:
        number = value if isinstance(value, Decimal) else Decimal(str(value))
    except Exception as exc:
        raise DomainError(f"{label} deve ser um número decimal válido.") from exc
    if not number.is_finite():
        raise DomainError(f"{label} deve ser finito.")
    return number


def parse_aware_datetime(value: str | datetime, label: str) -> datetime:
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise DomainError(f"{label} deve ser uma data e hora válida.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DomainError(f"{label} precisa informar o fuso horário.")
    return parsed


def quote_session(meter_start: str | Decimal, meter_end: str | Decimal, tariff: str | Decimal) -> SessionQuote:
    start = parse_decimal(meter_start, "Leitura inicial")
    end = parse_decimal(meter_end, "Leitura final")
    price = parse_decimal(tariff, "Tarifa")
    if start < 0 or end < 0:
        raise DomainError("As leituras do medidor não podem ser negativas.")
    if price < 0:
        raise DomainError("A tarifa não pode ser negativa.")
    if end < start:
        raise DomainError("A leitura final não pode ser menor que a inicial.")
    energy = end - start
    amount = (energy * price).quantize(CENT, rounding=ROUND_HALF_UP)
    cents = int(amount * 100)
    return SessionQuote(energy, price, amount, cents)


def local_month(value: str | datetime) -> str:
    parsed = parse_aware_datetime(value, "Data de encerramento")
    local = parsed.astimezone(ZoneInfo(TIMEZONE))
    return local.strftime("%Y-%m")


def local_now() -> datetime:
    return datetime.now(ZoneInfo(TIMEZONE)).replace(microsecond=0)
