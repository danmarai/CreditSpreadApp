from __future__ import annotations

from datetime import date, datetime
from typing import Any, ClassVar, Optional

from pydantic import BaseModel, Field, field_validator


class Position(BaseModel):
    allowed_statuses: ClassVar[set[str]] = {"OPEN", "CLOSING", "CLOSED"}

    position_id: str
    symbol: str
    short_strike: float
    long_strike: float
    expiration: date
    entry_credit: float
    contracts: int
    status: str
    exit_price: Optional[float] = None
    exit_date: Optional[date] = None
    exit_reason: Optional[str] = None
    iv_rank_at_entry: Optional[float] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in cls.allowed_statuses:
            raise ValueError(f"status must be one of {sorted(cls.allowed_statuses)}")
        return value

    @field_validator("short_strike", "long_strike", "entry_credit", "exit_price")
    @classmethod
    def validate_positive_floats(cls, value: Optional[float]) -> Optional[float]:
        if value is None:
            return value
        if value <= 0:
            raise ValueError("value must be positive")
        return value

    @field_validator("contracts")
    @classmethod
    def validate_contracts(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("contracts must be positive")
        return value

    @classmethod
    def from_sheet_row(cls, row: dict[str, Any]) -> "Position":
        return cls.model_validate(
            {
                "position_id": str(row.get("position_id", "")),
                "symbol": str(row.get("symbol", "")),
                "short_strike": row.get("short_strike"),
                "long_strike": row.get("long_strike"),
                "expiration": _parse_date(row.get("expiration")),
                "entry_credit": row.get("entry_credit"),
                "contracts": row.get("contracts"),
                "status": str(row.get("status", "")),
                "exit_price": _parse_optional_float(row.get("exit_price")),
                "exit_date": _parse_optional_date(row.get("exit_date")),
                "exit_reason": _parse_optional_str(row.get("exit_reason")),
                "iv_rank_at_entry": _parse_optional_float(row.get("iv_rank_at_entry")),
            }
        )

    def to_sheet_row(self) -> dict[str, Any]:
        return {
            "position_id": self.position_id,
            "symbol": self.symbol,
            "short_strike": self.short_strike,
            "long_strike": self.long_strike,
            "expiration": self.expiration.isoformat(),
            "entry_credit": self.entry_credit,
            "contracts": self.contracts,
            "status": self.status,
            "exit_price": self.exit_price if self.exit_price is not None else "",
            "exit_date": self.exit_date.isoformat() if self.exit_date else "",
            "exit_reason": self.exit_reason or "",
            "iv_rank_at_entry": (
                self.iv_rank_at_entry if self.iv_rank_at_entry is not None else ""
            ),
        }


class EventLogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str
    symbol: str
    position_id: Optional[str] = None
    message: str


def _parse_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise ValueError("expiration must be a date or ISO date string")


def _parse_optional_date(value: Any) -> Optional[date]:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise ValueError("date must be a date or ISO date string")


def _parse_optional_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    return float(value)


def _parse_optional_str(value: Any) -> Optional[str]:
    if value in (None, ""):
        return None
    return str(value)
