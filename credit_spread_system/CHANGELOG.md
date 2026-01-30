# Changelog

## 2026-01-30
- Task 1: Project scaffolding.
- Task 2: Configuration module and tests.
- Task 3: Google Sheets client and tests.
- Task 4: Google Sheets schema models and tests.
- Task 5: Alpaca API client and tests.
- Task 6: Market state module and tests.
- Task 7: Pricing module and tests.
- Task 8: Event log module and tests.
- Task 9: IV Rank module and tests.
- Task 10: Exit rules (profit/stop) and tests.
- Task 11: Exit rules (DTE/breach) and tests.
- Files added/updated: `credit_spread_system/__init__.py`, `credit_spread_system/app/__init__.py`, `credit_spread_system/app/main.py`, `credit_spread_system/tests/__init__.py`, `credit_spread_system/tests/test_config.py`, `credit_spread_system/tests/test_sheets_client.py`, `credit_spread_system/tests/test_models.py`, `credit_spread_system/tests/test_alpaca_client.py`, `credit_spread_system/tests/test_market_state.py`, `credit_spread_system/tests/test_pricing.py`, `credit_spread_system/tests/test_event_log.py`, `credit_spread_system/tests/test_iv_rank.py`, `credit_spread_system/tests/test_exit_rules_profit_stop.py`, `credit_spread_system/tests/test_exit_rules_dte_breach.py`, `credit_spread_system/config.py`, `credit_spread_system/sheets_client.py`, `credit_spread_system/models.py`, `credit_spread_system/alpaca_client.py`, `credit_spread_system/market_state.py`, `credit_spread_system/pricing.py`, `credit_spread_system/event_log.py`, `credit_spread_system/iv_rank.py`, `credit_spread_system/exit_rules.py`, `credit_spread_system/STATUS.md`, `credit_spread_system/CHANGELOG.md`, `.gitignore`, `.env.example`, `pyproject.toml`.
- Tests: `python3 -m pytest -q`, `python3 -m ruff check .`, `python3 -m mypy .`.
- Issues: Streamlit run requires port bind permissions; ran with escalated permissions. Pytest emitted Python 3.9 EOL warnings from google-auth.
