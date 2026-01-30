# Credit Spread Trading System — PRD (v1.1)

## 1. Purpose & Scope
This system is a decision-support and risk-monitoring tool for managing credit spread portfolios.
It does not auto-trade. Google Sheets is the source of truth.

### MVP Scope (Phase 1)
- Instruments: ETFs only
- Functions:
  - Monitor open credit spreads
  - Evaluate exits (price, time, risk)
  - Enforce disciplined entry gating via IV Rank
  - Surface portfolio-level risk warnings

### Explicit Non-Goals (MVP)
- No auto-trading
- No row moving between sheets
- No earnings filtering (ETFs only)

## 2. Source of Truth
- Single Google Sheet tab: Positions
- All trades remain in this tab
- Closed trades are reviewed by filtering status = CLOSED

## 3. Pricing & P/L Semantics
- Primary pricing: mid-price (bid+ask)/2
- Fallback pricing: last traded price
- Pricing method used is recorded internally

Spread value:
Current Spread Value = Short Leg Price − Long Leg Price

P/L:
P/L = (Entry Credit − Current Spread Value) × 100 × Contracts

## 4. Exit Rules
- Profit target: ≥50% max profit (advisory)
- Stop loss: loss ≥2× credit (strong advisory)
- Time exit: DTE ≤14 (advisory)
- Strike breach:
  - Close breach only
  - Evaluated end-of-day
  - 1% near-breach warning band

## 5. Volatility (IV Rank)
- True IV Rank, system computed
- Data source: Alpaca (paid)
- Formula:
  (Current IV − 52w Low IV) / (52w High IV − 52w Low IV)

Behavior:
- If IV Rank < min_iv_rank:
  - Block new trade recommendations
  - Log event
- No effect on exits

## 6. Portfolio Risk Controls
- Track total P/L, deployment, concentration
- Daily/weekly stop breach:
  - Alert
  - Recommend closing highest-risk spread
  - No forced closures

## 7. Market Hours & Data Freshness
- Show after-hours prices if available
- Warn on stale data
- Degrade gracefully on API failure

## 8. Logging
- Event_Log tab in Google Sheets
- Retention: 7 days
- Logged events include:
  - IV Rank blocks
  - Portfolio stop alerts
  - Pricing fallbacks
  - Stale data warnings

## 9. Phase 2 Roadmap
- Universe selector:
  1. ETFs
  2. Large-cap stocks
  3. All optionable underlyings
- Earnings filtering (Phase 2 only):
  - Source: Financial Modeling Prep (free)
  - Manual override allowed
  - Block new trades only
