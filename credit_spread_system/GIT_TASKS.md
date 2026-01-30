# Credit Spread System — Git Tasks

## Overview

19 tasks following logical implementation sequence. Each task is a self-contained unit of work.

| #   | Task                            | Dependencies |
| --- | ------------------------------- | ------------ |
| 1   | Project Scaffolding             | None         |
| 2   | Configuration Module            | Task 1       |
| 3   | Google Sheets Connection        | Task 2       |
| 4   | Google Sheets Schema Models     | Task 3       |
| 5   | Alpaca API Client               | Task 2       |
| 6   | Market State Module             | Task 2       |
| 7   | Pricing Module                  | Task 5       |
| 8   | Event Log Module                | Task 3, 4    |
| 9   | IV Rank Module                  | Task 5, 8    |
| 10  | Exit Rules - Profit/Stop        | Task 7       |
| 11  | Exit Rules - DTE/Breach         | Task 10      |
| 12  | Exit Rules - Unified Evaluator  | Task 11      |
| 13  | Portfolio Risk Module           | Task 7, 12   |
| 14  | Data Aggregation Layer          | Tasks 3-13   |
| 15  | Streamlit UI - Layout & Summary | Task 14      |
| 16  | Streamlit UI - Positions Table  | Task 15      |
| 17  | Streamlit UI - Position Detail  | Task 16      |
| 18  | Streamlit UI - IV Rank Display  | Task 17      |
| 19  | Integration Testing & Docs      | Tasks 1-18   |

---

## Git Task 1: Project Scaffolding

**Files to create:**

- `credit_spread_system/` (directory)
- `credit_spread_system/__init__.py`
- `credit_spread_system/app/` (directory)
- `credit_spread_system/app/__init__.py`
- `credit_spread_system/app/main.py` (Streamlit entry point stub)
- `credit_spread_system/tests/` (directory)
- `credit_spread_system/tests/__init__.py`
- `pyproject.toml` (dependencies: streamlit, gspread, alpaca-py, python-dotenv, pytest)
- `.gitignore` (Python, .env, venv, **pycache**)
- `.env.example` (template for API keys)
- `credit_spread_system/STATUS.md`
- `credit_spread_system/CHANGELOG.md`

**Implementation:**

1. Create folder structure
2. Add pyproject.toml with all dependencies
3. Add .gitignore with Python defaults + .env
4. Create stub main.py that shows "Credit Spread System - Coming Soon"

**Tests:** `pytest` runs without errors; `streamlit run app/main.py` launches

**Acceptance:** Directory structure exists, dependencies installable, Streamlit stub runs

---

## Git Task 2: Configuration Module

**Files to create:**

- `credit_spread_system/config.py`
- `credit_spread_system/tests/test_config.py`

**Implementation:**

1. Load environment variables from `.env`
2. Define config dataclass with: `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `GOOGLE_SHEETS_CREDS_PATH`, `SPREADSHEET_ID`
3. Add constants: `PROFIT_TARGET_PCT=0.50`, `STOP_LOSS_MULTIPLE=2.0`, `DTE_WARNING_DAYS=14`, `NEAR_BREACH_PCT=0.01`, `MIN_IV_RANK=30`, `EVENT_LOG_RETENTION_DAYS=7`

**Tests:**

- Missing required env var raises clear error
- Config loads correctly with valid .env

**Edge cases:** Missing .env file, missing individual keys

**Acceptance:** Config module loads and validates all settings

---

## Git Task 3: Google Sheets Connection

**Files to create:**

- `credit_spread_system/sheets_client.py`
- `credit_spread_system/tests/test_sheets_client.py`

**Implementation:**

1. Initialize gspread client with service account credentials
2. Connect to spreadsheet by ID
3. Functions: `get_worksheet(name)`, `get_all_positions()`, `update_position(position_id, data)`, `append_event_log(event)`
4. Handle connection errors gracefully (log warning, return empty/None)

**Tests:**

- Mock gspread client
- Test connection failure handling
- Test data retrieval and update functions

**Edge cases:** Invalid credentials, spreadsheet not found, worksheet not found, rate limiting

**Acceptance:** Can connect to sheets, read positions, write events

---

## Git Task 4: Google Sheets Schema Models

**Files to create:**

- `credit_spread_system/models.py`
- `credit_spread_system/tests/test_models.py`

**Implementation:**

1. Pydantic models for:
   - `Position` (position_id, symbol, short_strike, long_strike, expiration, entry_credit, contracts, status, exit_price, exit_date, exit_reason, iv_rank_at_entry)
   - `EventLogEntry` (timestamp, event_type, symbol, position_id, message)
2. Validation: expiration is date, strikes are positive floats, status in [OPEN, CLOSING, CLOSED]
3. Helper: `Position.from_sheet_row()`, `Position.to_sheet_row()`

**Tests:**

- Valid position parses correctly
- Invalid data raises ValidationError
- Round-trip sheet row conversion

**Edge cases:** Missing optional fields, malformed dates, negative values

**Acceptance:** Models validate and convert sheet data correctly

---

## Git Task 5: Alpaca API Client

**Files to create:**

- `credit_spread_system/alpaca_client.py`
- `credit_spread_system/tests/test_alpaca_client.py`

**Implementation:**

1. Initialize Alpaca options client with API keys
2. Function: `get_option_quote(symbol, expiration, strike, option_type)` → returns bid, ask, last
3. Function: `get_underlying_price(symbol)` → returns current price
4. Cache quotes for 60 seconds (configurable)
5. Handle API errors gracefully (return None, log warning)

**Tests:**

- Mock Alpaca client responses
- Test cache behavior
- Test error handling (API down, invalid symbol)

**Edge cases:** Rate limits, after-hours quotes, missing data, API timeout

**Acceptance:** Can fetch option quotes and underlying prices with caching

---

## Git Task 6: Market State Module

**Files to create:**

- `credit_spread_system/market_state.py`
- `credit_spread_system/tests/test_market_state.py`

**Implementation:**

1. `is_market_open()` → bool (check current time vs NYSE hours, account for holidays)
2. `is_after_hours()` → bool
3. `is_quote_stale(quote_timestamp, max_age_seconds=300)` → bool
4. `get_market_status()` → returns dict with is_open, is_after_hours, message

**Tests:**

- Test during market hours (mocked time)
- Test after hours
- Test weekend
- Test stale quote detection

**Edge cases:** Holidays, early close days, daylight saving transitions

**Acceptance:** Correctly identifies market state and quote staleness

---

## Git Task 7: Pricing Module

**Files to create:**

- `credit_spread_system/pricing.py`
- `credit_spread_system/tests/test_pricing.py`

**Implementation:**

1. `get_mid_price(bid, ask)` → (bid + ask) / 2
2. `get_option_price(quote)` → mid if bid/ask valid, else last (fallback), emit event if fallback used
3. `get_spread_value(short_leg_price, long_leg_price)` → short - long
4. `calculate_pl(entry_credit, current_spread_value, contracts)` → (entry_credit - spread_value) _ 100 _ contracts
5. Track pricing method used (MID vs LAST) in return value

**Tests:**

- Mid price calculation
- Fallback to last when bid/ask missing
- P/L calculation (profit and loss cases)
- Spread value calculation

**Edge cases:** Zero bid, missing ask, negative spread value, stale quotes

**Acceptance:** Pricing calculates correctly with proper fallback logic

---

## Git Task 8: Event Log Module

**Files to create:**

- `credit_spread_system/event_log.py`
- `credit_spread_system/tests/test_event_log.py`

**Implementation:**

1. `log_event(event_type, symbol, position_id, message)` → appends to Event_Log sheet
2. Event types: `IV_RANK_BLOCK`, `PORTFOLIO_STOP_ALERT`, `PRICING_FALLBACK`, `STALE_DATA_WARNING`, `API_ERROR`
3. `prune_old_events(retention_days=7)` → deletes events older than retention
4. Timestamp in ISO format

**Tests:**

- Event appends correctly (mocked sheets)
- Pruning removes old events
- Event types are validated

**Edge cases:** Sheet write failure, empty event log, pruning large datasets

**Acceptance:** Events logged to sheet, old events pruned

---

## Git Task 9: IV Rank Module

**Files to create:**

- `credit_spread_system/iv_rank.py`
- `credit_spread_system/tests/test_iv_rank.py`

**Implementation:**

1. `fetch_historical_iv(symbol, days=365)` → get IV history from Alpaca
2. `calculate_iv_rank(current_iv, iv_history)` → (current - 52w_low) / (52w_high - 52w_low)
3. `get_iv_rank(symbol)` → returns IV Rank (0-100) or None if unavailable
4. Cache IV Rank for 1 hour
5. `should_block_new_trade(symbol, min_iv_rank=30)` → bool, logs event if blocked

**Tests:**

- IV Rank calculation at extremes (0%, 50%, 100%)
- Cache behavior
- Block logic when IV Rank too low
- Handle missing IV data

**Edge cases:** No IV history, insufficient data points, API failure, very low/high IV

**Acceptance:** IV Rank calculates correctly, trade blocking works

---

## Git Task 10: Exit Rules - Profit Target & Stop Loss

**Files to create:**

- `credit_spread_system/exit_rules.py`
- `credit_spread_system/tests/test_exit_rules.py`

**Implementation:**

1. `check_profit_target(entry_credit, current_spread_value, target_pct=0.50)` → bool, message
2. `check_stop_loss(entry_credit, current_spread_value, stop_multiple=2.0)` → bool, message
3. Both return `(triggered: bool, current_pct: float, message: str)`

**Tests:**

- Profit target at 49%, 50%, 51%
- Stop loss at 1.9x, 2.0x, 2.1x credit
- Edge cases with zero values

**Edge cases:** Very small credits, exactly at threshold

**Acceptance:** Profit target and stop loss thresholds detected correctly

---

## Git Task 11: Exit Rules - DTE & Breach Detection

**Files to add to:**

- `credit_spread_system/exit_rules.py`
- `credit_spread_system/tests/test_exit_rules.py`

**Implementation:**

1. `check_dte(expiration_date, warning_days=14)` → (is_warning: bool, dte: int, message: str)
2. `check_strike_breach(underlying_price, short_strike, spread_type)` → (breached: bool, message: str)
3. `check_near_breach(underlying_price, short_strike, spread_type, band_pct=0.01)` → (near: bool, distance_pct: float, message: str)
4. spread_type: "PUT" or "CALL" (determines breach direction)

**Tests:**

- DTE at 15, 14, 13 days
- Strike breach for puts (price below short strike)
- Strike breach for calls (price above short strike)
- Near-breach at 0.5%, 1%, 1.5% from strike

**Edge cases:** Expiration today, negative DTE, price exactly at strike

**Acceptance:** All exit conditions detected correctly

---

## Git Task 12: Exit Rules - Unified Evaluator

**Files to add to:**

- `credit_spread_system/exit_rules.py`
- `credit_spread_system/tests/test_exit_rules.py`

**Implementation:**

1. `evaluate_position(position, current_spread_value, underlying_price)` → returns prioritized action
2. Action enum: `CLOSE_BREACH`, `STOP_LOSS`, `TAKE_PROFIT`, `CLOSE_DTE`, `EVALUATE`, `HOLD`
3. Priority order: breach > stop_loss > take_profit > dte_warning > hold
4. Returns: `(action: Action, details: dict)` with all relevant metrics

**Tests:**

- Multiple conditions triggered, highest priority returned
- Single condition triggered
- No conditions triggered → HOLD

**Edge cases:** All conditions triggered simultaneously

**Acceptance:** Position evaluation returns correct prioritized action

---

## Git Task 13: Portfolio Risk Module

**Files to create:**

- `credit_spread_system/portfolio_risk.py`
- `credit_spread_system/tests/test_portfolio_risk.py`

**Implementation:**

1. `calculate_total_pl(positions, current_values)` → aggregate P/L
2. `calculate_deployment(positions, portfolio_value)` → % of capital deployed
3. `check_daily_stop(total_pl, daily_limit)` → (breached: bool, message: str)
4. `check_weekly_stop(total_pl, weekly_limit)` → (breached: bool, message: str)
5. `rank_positions_by_risk(positions, current_values)` → sorted list, highest risk first
6. Risk ranking factors: % of max loss realized, proximity to breach

**Tests:**

- Total P/L aggregation
- Deployment calculation
- Stop breach detection
- Risk ranking order

**Edge cases:** No positions, single position, all positions at max loss

**Acceptance:** Portfolio metrics calculate correctly, risk ranking works

---

## Git Task 14: Data Aggregation Layer

**Files to create:**

- `credit_spread_system/data_service.py`
- `credit_spread_system/tests/test_data_service.py`

**Implementation:**

1. `get_enriched_positions()` → fetches positions from sheets, enriches with:
   - Current option prices (both legs)
   - Current spread value
   - Current P/L
   - Current underlying price
   - All exit rule evaluations
   - Pricing method used (MID/LAST)
2. `get_portfolio_summary()` → returns total P/L, deployment, stop status, risk ranking
3. `get_market_context()` → returns market state, quote staleness warnings
4. Handles all API failures gracefully with warnings

**Tests:**

- Full enrichment with mocked dependencies
- Graceful degradation on API failure
- Warning aggregation

**Edge cases:** Partial API failures, all positions closed, empty portfolio

**Acceptance:** Data service aggregates all data correctly with graceful degradation

---

## Git Task 15: Streamlit UI - Layout & Portfolio Summary

**Files to modify:**

- `credit_spread_system/app/main.py`

**Files to create:**

- `credit_spread_system/app/components/__init__.py`
- `credit_spread_system/app/components/portfolio_summary.py`

**Implementation:**

1. Main page layout with title, refresh button
2. Market status indicator (open/closed/after-hours)
3. Portfolio summary cards: Total P/L, Deployment %, Position count
4. Warning banners for: stale data, API errors, portfolio stop breach

**Tests:** Manual testing checklist (Streamlit not easily unit tested)

**Acceptance:** Dashboard displays summary data, warnings appear when appropriate

---

## Git Task 16: Streamlit UI - Positions Table

**Files to create:**

- `credit_spread_system/app/components/positions_table.py`

**Implementation:**

1. Table showing all open positions with columns:
   - Symbol, Strikes, Expiration, DTE
   - Entry Credit, Current Value, P/L ($), P/L (%)
   - Action Required (colored badge)
2. Sortable by any column
3. Action Required positions highlighted/grouped at top
4. Color coding: green (profit), red (loss), yellow (warning)

**Tests:** Manual testing checklist

**Acceptance:** Positions display correctly with proper formatting and grouping

---

## Git Task 17: Streamlit UI - Position Detail View

**Files to create:**

- `credit_spread_system/app/components/position_detail.py`

**Implementation:**

1. Expandable detail view for each position
2. Shows: all exit rule evaluations, pricing method used, quote timestamps
3. Action recommendation with explanation
4. Quick links/buttons for common actions (mark as closing)

**Tests:** Manual testing checklist

**Acceptance:** Detail view shows all relevant position data

---

## Git Task 18: Streamlit UI - IV Rank & Entry Gating

**Files to create:**

- `credit_spread_system/app/components/iv_rank_display.py`

**Implementation:**

1. IV Rank display for watchlist symbols
2. Visual indicator: green (>50), yellow (30-50), red (<30)
3. "Trade Blocked" warning when IV Rank too low
4. Event log display (last 10 events)

**Tests:** Manual testing checklist

**Acceptance:** IV Rank displays correctly, blocking warnings appear

---

## Git Task 19: Integration Testing & Documentation

**Files to create:**

- `credit_spread_system/tests/test_integration.py`
- `README.md` (project root)

**Implementation:**

1. End-to-end integration tests with mocked external services
2. Test full flow: load positions → enrich → evaluate → display
3. README with: setup instructions, environment variables, usage guide

**Tests:**

- Full integration test suite
- All edge cases covered

**Acceptance:** All tests pass, README complete, system runs end-to-end
