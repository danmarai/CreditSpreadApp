from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from credit_spread_system.event_log import EVENT_TYPES, log_event, prune_old_events


class FakeWorksheet:
    def __init__(self, rows: list[dict[str, str]] | None = None) -> None:
        self.rows = rows or []
        self.deleted_rows: list[int] = []
        self.appended: list[list[str]] = []

    def get_all_records(self):
        return self.rows

    def delete_rows(self, index: int):
        self.deleted_rows.append(index)

    def row_values(self, _row: int):
        return ["timestamp", "event_type", "symbol", "position_id", "message"]

    def append_row(self, row):
        self.appended.append(row)


class FakeSheetsClient:
    def __init__(self, worksheet: FakeWorksheet | None) -> None:
        self._worksheet = worksheet

    def get_worksheet(self, _name: str):
        return self._worksheet

    def append_event_log(self, event):
        if not self._worksheet:
            return False
        headers = self._worksheet.row_values(1)
        row = [event.get(header, "") for header in headers]
        self._worksheet.append_row(row)
        return True


def test_log_event_appends_row():
    worksheet = FakeWorksheet()
    client = FakeSheetsClient(worksheet)

    assert log_event(
        event_type="PRICING_FALLBACK",
        symbol="SPY",
        position_id="1",
        message="test",
        sheets_client=client,
    )

    assert len(worksheet.appended) == 1
    assert worksheet.appended[0][1] == "PRICING_FALLBACK"


def test_log_event_invalid_type():
    worksheet = FakeWorksheet()
    client = FakeSheetsClient(worksheet)

    with pytest.raises(ValueError):
        log_event(
            event_type="INVALID",
            symbol="SPY",
            position_id=None,
            message="test",
            sheets_client=client,
        )


def test_prune_old_events_removes_old_rows():
    now = datetime.now(timezone.utc)
    old = (now - timedelta(days=10)).isoformat()
    recent = (now - timedelta(days=2)).isoformat()

    worksheet = FakeWorksheet(
        rows=[
            {"timestamp": old, "event_type": "API_ERROR", "symbol": "SPY"},
            {"timestamp": recent, "event_type": "API_ERROR", "symbol": "SPY"},
        ]
    )
    client = FakeSheetsClient(worksheet)

    deleted = prune_old_events(retention_days=7, sheets_client=client)

    assert deleted == 1
    assert worksheet.deleted_rows == [2]


def test_event_types_contains_expected():
    assert "PRICING_FALLBACK" in EVENT_TYPES
