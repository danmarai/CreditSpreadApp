from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import gspread

from credit_spread_system.config import load_config

logger = logging.getLogger(__name__)


@dataclass
class SheetsClient:
    spreadsheet: Any | None

    @classmethod
    def from_env(cls) -> "SheetsClient":
        config = load_config()
        return cls.from_credentials(
            creds_path=config.google_sheets_creds_path,
            spreadsheet_id=config.spreadsheet_id,
        )

    @classmethod
    def from_credentials(cls, creds_path: str, spreadsheet_id: str) -> "SheetsClient":
        try:
            client = gspread.service_account(filename=creds_path)
            spreadsheet = client.open_by_key(spreadsheet_id)
            return cls(spreadsheet=spreadsheet)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to initialize Google Sheets client: %s", exc)
            return cls(spreadsheet=None)

    def get_worksheet(self, name: str) -> Any | None:
        if not self.spreadsheet:
            return None
        try:
            return self.spreadsheet.worksheet(name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Worksheet not found or unavailable (%s): %s", name, exc)
            return None

    def get_all_positions(self) -> list[dict[str, Any]]:
        worksheet = self.get_worksheet("Positions")
        if not worksheet:
            return []
        try:
            return worksheet.get_all_records()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to read positions: %s", exc)
            return []

    def update_position(self, position_id: str, data: dict[str, Any]) -> bool:
        worksheet = self.get_worksheet("Positions")
        if not worksheet:
            return False
        try:
            cell = worksheet.find(str(position_id))
            headers = worksheet.row_values(1)
            for key, value in data.items():
                if key in headers:
                    col = headers.index(key) + 1
                    worksheet.update_cell(cell.row, col, value)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to update position %s: %s", position_id, exc)
            return False

    def append_event_log(self, event: dict[str, Any]) -> bool:
        worksheet = self.get_worksheet("Event_Log")
        if not worksheet:
            return False
        try:
            headers = worksheet.row_values(1)
            row = [event.get(header, "") for header in headers]
            worksheet.append_row(row)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to append event log: %s", exc)
            return False
