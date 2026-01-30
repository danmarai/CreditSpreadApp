from __future__ import annotations

import logging
from dataclasses import dataclass

from credit_spread_system.alpaca_client import AlpacaClient
from credit_spread_system.exit_rules import evaluate_position
from credit_spread_system.market_state import get_market_status
from credit_spread_system.models import Position
from credit_spread_system.portfolio_risk import (
    calculate_deployment,
    calculate_total_pl,
    check_daily_stop,
    check_weekly_stop,
    rank_positions_by_risk,
)
from credit_spread_system.pricing import get_option_price, get_spread_value
from credit_spread_system.sheets_client import SheetsClient

logger = logging.getLogger(__name__)


@dataclass
class EnrichedPosition:
    position: Position
    short_leg_price: float | None
    long_leg_price: float | None
    spread_value: float | None
    current_pl: float | None
    underlying_price: float | None
    pricing_methods: dict[str, str]
    exit_action: str
    exit_details: dict[str, object]


class DataService:
    def __init__(self, sheets: SheetsClient, alpaca: AlpacaClient) -> None:
        self.sheets = sheets
        self.alpaca = alpaca

    def get_enriched_positions(self) -> list[EnrichedPosition]:
        positions = [Position.from_sheet_row(row) for row in self.sheets.get_all_positions()]
        enriched: list[EnrichedPosition] = []

        for position in positions:
            try:
                symbol = position.symbol
                expiration = position.expiration.isoformat()
                short_quote = self.alpaca.get_option_quote(
                    symbol, expiration, position.short_strike, "put"
                )
                long_quote = self.alpaca.get_option_quote(
                    symbol, expiration, position.long_strike, "put"
                )
                short_price = get_option_price(short_quote)
                long_price = get_option_price(long_quote)
                spread_value = get_spread_value(short_price.price, long_price.price)

                current_pl = (
                    (position.entry_credit - spread_value) * 100 * position.contracts
                    if spread_value is not None
                    else None
                )

                underlying_price = self.alpaca.get_underlying_price(symbol)

                exit_action, exit_details = evaluate_position(
                    position=position,
                    current_spread_value=spread_value,
                    underlying_price=underlying_price,
                )

                enriched.append(
                    EnrichedPosition(
                        position=position,
                        short_leg_price=short_price.price,
                        long_leg_price=long_price.price,
                        spread_value=spread_value,
                        current_pl=current_pl,
                        underlying_price=underlying_price,
                        pricing_methods={
                            "short": short_price.method,
                            "long": long_price.method,
                        },
                        exit_action=str(exit_action),
                        exit_details=exit_details,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to enrich position %s: %s", position, exc)
                continue

        return enriched

    def get_portfolio_summary(self, portfolio_value: float) -> dict[str, object]:
        rows = self.sheets.get_all_positions()
        positions = [Position.from_sheet_row(row) for row in rows]
        current_values: dict[str, float] = {}
        for row in rows:
            position_id = str(row.get("position_id", ""))
            if not position_id:
                continue
            raw_value = row.get("current_spread_value")
            if raw_value is None:
                continue
            try:
                current_values[position_id] = float(raw_value)
            except (TypeError, ValueError):
                continue

        total_pl = calculate_total_pl(positions, current_values)
        deployment = calculate_deployment(positions, portfolio_value)

        daily_stop = check_daily_stop(total_pl, daily_limit=500)
        weekly_stop = check_weekly_stop(total_pl, weekly_limit=1000)

        ranked = rank_positions_by_risk(positions, current_values, {})

        return {
            "total_pl": total_pl,
            "deployment": deployment,
            "daily_stop": daily_stop,
            "weekly_stop": weekly_stop,
            "risk_ranked_positions": ranked,
        }

    def get_market_context(self) -> dict[str, object]:
        market_status = get_market_status()
        return {"market_status": market_status, "quotes_stale": False}
