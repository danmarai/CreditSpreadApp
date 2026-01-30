from types import SimpleNamespace
from unittest.mock import MagicMock

from credit_spread_system.sheets_client import SheetsClient


def test_connection_failure_returns_empty(monkeypatch):
    def _raise(*_args, **_kwargs):
        raise Exception("boom")

    monkeypatch.setattr("credit_spread_system.sheets_client.gspread.service_account", _raise)

    client = SheetsClient.from_credentials("/tmp/creds.json", "sheet123")

    assert client.spreadsheet is None
    assert client.get_worksheet("Positions") is None
    assert client.get_all_positions() == []


def test_get_all_positions_success():
    worksheet = MagicMock()
    worksheet.get_all_records.return_value = [{"position_id": "1"}]

    spreadsheet = MagicMock()
    spreadsheet.worksheet.return_value = worksheet

    client = SheetsClient(spreadsheet=spreadsheet)
    result = client.get_all_positions()

    assert result == [{"position_id": "1"}]
    spreadsheet.worksheet.assert_called_with("Positions")


def test_update_position_updates_matching_headers():
    worksheet = MagicMock()
    worksheet.find.return_value = SimpleNamespace(row=3)
    worksheet.row_values.return_value = ["position_id", "status", "exit_reason"]

    spreadsheet = MagicMock()
    spreadsheet.worksheet.return_value = worksheet

    client = SheetsClient(spreadsheet=spreadsheet)
    updated = client.update_position("1", {"status": "CLOSED", "exit_reason": "Target"})

    assert updated is True
    worksheet.update_cell.assert_any_call(3, 2, "CLOSED")
    worksheet.update_cell.assert_any_call(3, 3, "Target")


def test_append_event_log_appends_row():
    worksheet = MagicMock()
    worksheet.row_values.return_value = ["timestamp", "event_type", "symbol"]

    spreadsheet = MagicMock()
    spreadsheet.worksheet.return_value = worksheet

    client = SheetsClient(spreadsheet=spreadsheet)
    success = client.append_event_log(
        {"timestamp": "2026-01-30", "event_type": "TEST", "symbol": "SPY"}
    )

    assert success is True
    worksheet.append_row.assert_called_once_with(["2026-01-30", "TEST", "SPY"])
