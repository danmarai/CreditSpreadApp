# Credit Spread System

## Overview
Decision-support and risk-monitoring dashboard for managing credit spread portfolios. The system reads positions from Google Sheets, fetches market data from Alpaca, and surfaces exit signals and portfolio risk warnings. No auto-trading.

## Setup
1. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   python3 -m pip install -e .
   ```
2. Create a `.env` file from `.env.example` and fill in credentials.
3. Ensure your Google Sheet has a `Positions` tab and an `Event_Log` tab with headers matching the PRD.

## Run
```bash
python3 -m streamlit run credit_spread_system/app/main.py
```

## Tests
```bash
python3 -m pytest -q
python3 -m ruff check .
python3 -m mypy .
```

## Notes
- Market hours use NYSE calendar.
- IV Rank blocks new trade recommendations only.
- Pricing uses mid-price, falls back to last.
