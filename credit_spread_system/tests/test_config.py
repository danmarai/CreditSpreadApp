import pytest

from credit_spread_system.config import Config, load_config


def test_load_config_missing_env_vars_raises(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("")

    for key in (
        "ALPACA_API_KEY",
        "ALPACA_SECRET_KEY",
        "GOOGLE_SHEETS_CREDS_PATH",
        "SPREADSHEET_ID",
    ):
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(ValueError) as excinfo:
        load_config(env_path=str(env_file))

    message = str(excinfo.value)
    assert "Missing required environment variables" in message
    assert "ALPACA_API_KEY" in message


def test_load_config_success(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "ALPACA_API_KEY=key",
                "ALPACA_SECRET_KEY=secret",
                "GOOGLE_SHEETS_CREDS_PATH=/tmp/creds.json",
                "SPREADSHEET_ID=sheet123",
            ]
        )
    )

    for key in (
        "ALPACA_API_KEY",
        "ALPACA_SECRET_KEY",
        "GOOGLE_SHEETS_CREDS_PATH",
        "SPREADSHEET_ID",
    ):
        monkeypatch.delenv(key, raising=False)

    config = load_config(env_path=str(env_file))

    assert isinstance(config, Config)
    assert config.alpaca_api_key == "key"
    assert config.alpaca_secret_key == "secret"
    assert config.google_sheets_creds_path == "/tmp/creds.json"
    assert config.spreadsheet_id == "sheet123"
