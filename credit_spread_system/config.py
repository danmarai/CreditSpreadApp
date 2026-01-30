from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable

from dotenv import load_dotenv

PROFIT_TARGET_PCT = 0.50
STOP_LOSS_MULTIPLE = 2.0
DTE_WARNING_DAYS = 14
NEAR_BREACH_PCT = 0.01
MIN_IV_RANK = 30
EVENT_LOG_RETENTION_DAYS = 7

REQUIRED_ENV_VARS = (
    "ALPACA_API_KEY",
    "ALPACA_SECRET_KEY",
    "GOOGLE_SHEETS_CREDS_PATH",
    "SPREADSHEET_ID",
)


@dataclass(frozen=True)
class Config:
    alpaca_api_key: str
    alpaca_secret_key: str
    google_sheets_creds_path: str
    spreadsheet_id: str


def _missing_vars(required: Iterable[str]) -> list[str]:
    missing = []
    for key in required:
        if not os.getenv(key):
            missing.append(key)
    return missing


def load_config(env_path: str | None = None) -> Config:
    load_dotenv(env_path)

    missing = _missing_vars(REQUIRED_ENV_VARS)
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return Config(
        alpaca_api_key=os.environ["ALPACA_API_KEY"],
        alpaca_secret_key=os.environ["ALPACA_SECRET_KEY"],
        google_sheets_creds_path=os.environ["GOOGLE_SHEETS_CREDS_PATH"],
        spreadsheet_id=os.environ["SPREADSHEET_ID"],
    )
