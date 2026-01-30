# Credit Spread Trading System — Technical Plan (v1.1)

## Architecture
- Streamlit UI
- Google Sheets API
- Alpaca Options & Greeks API

## Core Modules
pricing.py
- Fetch bid/ask/last
- Compute mid-price
- Apply fallback logic
- Emit pricing fallback events

iv_rank.py
- Fetch historical IV
- Compute rolling 52-week min/max
- Compute IV Rank
- Cache results
- Block trades if unavailable

exit_rules.py
- Profit target evaluator
- Stop-loss evaluator
- DTE evaluator
- EOD close-breach evaluator
- Near-breach detector (1%)

portfolio_risk.py
- Aggregate P/L
- Detect daily/weekly stop breaches
- Rank positions by risk
- Emit recommendations only

market_state.py
- Market open/closed detection
- After-hours handling
- Stale data detection

event_log.py
- Append events to Event_Log sheet
- Enforce 7-day retention

## Google Sheets Schema
Positions:
- position_id
- symbol
- short_strike
- long_strike
- expiration
- entry_credit
- contracts
- status
- exit_price
- exit_date
- exit_reason
- iv_rank_at_entry

Event_Log:
- timestamp
- event_type
- symbol
- position_id
- message

## Explicit MVP Constraints
- No row moving
- No earnings enforcement
- No auto-closing trades
