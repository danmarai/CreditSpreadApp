# Integration Testing

## Smoke Test Checklist
1. Set required env vars in `.env`:
   - `ALPACA_API_KEY`
   - `ALPACA_SECRET_KEY`
   - `GOOGLE_SHEETS_CREDS_PATH`
   - `SPREADSHEET_ID`
2. Verify Google Sheets tabs:
   - `Positions`
   - `Event_Log`
3. Run:
   ```bash
   python3 -m pytest -q
   python3 -m ruff check .
   python3 -m mypy .
   python3 -m streamlit run credit_spread_system/app/main.py
   ```
4. Confirm UI loads and shows:
   - Portfolio summary
   - Market context
   - Positions table
   - Position detail
   - IV Rank card

## Manual API Validation
- Confirm that Alpaca option quotes return bid/ask/last.
- Validate that Google Sheets updates append to `Event_Log`.
- Ensure stale quote warnings do not crash the app.
