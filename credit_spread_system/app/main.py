from __future__ import annotations

import logging
from datetime import datetime

import streamlit as st

from credit_spread_system.alpaca_client import AlpacaClient
from credit_spread_system.config import load_config
from credit_spread_system.data_service import DataService
from credit_spread_system.iv_rank import IvRankService
from credit_spread_system.sheets_client import SheetsClient

logger = logging.getLogger(__name__)


def _apply_theme() -> None:
    st.markdown(
        """
        <style>
        .main { background: radial-gradient(circle at top left, #f7f2ea, #f0f4f8); }
        h1, h2, h3 { font-family: "Georgia", "Times New Roman", serif; }
        .metric-label { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em; }
        .card { background: #ffffff; border-radius: 12px; padding: 1.2rem; box-shadow: 0 10px 30px rgba(0,0,0,0.06); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _build_header() -> None:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Credit Spread System")
        st.caption("Decision-support dashboard — ETFs only")
    with col2:
        st.markdown(
            f"<div class='card'><div class='metric-label'>Last Refresh</div><div>{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</div></div>",
            unsafe_allow_html=True,
        )


def _load_services() -> tuple[DataService | None, AlpacaClient | None]:
    try:
        load_config()
        sheets = SheetsClient.from_env()
        alpaca = AlpacaClient.from_env()
        return DataService(sheets, alpaca), alpaca
    except Exception as exc:  # noqa: BLE001
        st.warning("Configuration missing or invalid. Showing empty dashboard.")
        logger.warning("Failed to initialize services: %s", exc)
        return None, None


def _render_summary(data_service: DataService | None) -> None:
    st.subheader("Portfolio Summary")
    summary_cols = st.columns(4)

    total_pl = 0.0
    deployment = 0.0
    daily_status = "OK"
    weekly_status = "OK"

    if data_service:
        summary = data_service.get_portfolio_summary(portfolio_value=100000)
        total_pl_value = summary.get("total_pl", 0.0)
        deployment_value = summary.get("deployment", 0.0)
        total_pl = float(total_pl_value) if isinstance(total_pl_value, (int, float)) else 0.0
        deployment = float(deployment_value) if isinstance(deployment_value, (int, float)) else 0.0
        daily_stop = summary.get("daily_stop")
        weekly_stop = summary.get("weekly_stop")
        daily_status = "BREACH" if getattr(daily_stop, "breached", False) else "OK"
        weekly_status = "BREACH" if getattr(weekly_stop, "breached", False) else "OK"

    summary_cols[0].metric("Total P/L", f"${total_pl:,.2f}")
    summary_cols[1].metric("Deployment", f"{deployment * 100:.1f}%")
    summary_cols[2].metric("Daily Stop", daily_status)
    summary_cols[3].metric("Weekly Stop", weekly_status)


def _render_iv_rank(alpaca: AlpacaClient | None) -> None:
    st.subheader("IV Rank")
    if alpaca is None:
        st.info("IV Rank unavailable. Configure Alpaca credentials.")
        return

    symbol = st.text_input("IV Rank Symbol", value="SPY")
    if not symbol:
        st.info("Enter a symbol to view IV Rank.")
        return

    service = IvRankService()
    result = service.get_iv_rank(symbol.upper(), alpaca)

    if result.iv_rank is None:
        st.warning(result.reason)
        return

    status = "BLOCKED" if result.blocked else "OK"
    st.metric("IV Rank", f"{result.iv_rank:.2f}", help=f"Status: {status}")


def _render_market_context(data_service: DataService | None) -> None:
    st.subheader("Market Context")
    context = data_service.get_market_context() if data_service else {"market_status": {"message": "Unknown"}}
    status = context.get("market_status") if isinstance(context, dict) else {"message": "Unknown"}
    message = status.get("message", "Unknown") if isinstance(status, dict) else "Unknown"
    st.info(message)


def _render_positions_table(data_service: DataService | None) -> list:
    st.subheader("Positions")
    if not data_service:
        st.write("No data available. Configure environment variables to load positions.")
        return []

    positions = data_service.get_enriched_positions()
    if not positions:
        st.write("No positions found.")
        return []

    table_rows = []
    for item in positions:
        table_rows.append(
            {
                "Position ID": item.position.position_id,
                "Symbol": item.position.symbol,
                "Short Strike": item.position.short_strike,
                "Long Strike": item.position.long_strike,
                "Expiration": item.position.expiration.isoformat(),
                "Spread Value": item.spread_value,
                "P/L": item.current_pl,
                "Exit Action": item.exit_action,
            }
        )

    st.dataframe(table_rows, use_container_width=True)
    return positions


def _render_position_detail(positions: list) -> None:
    st.subheader("Position Detail")
    if not positions:
        st.write("Select a position once data is available.")
        return

    position_ids = [item.position.position_id for item in positions]
    selected_id = st.selectbox("Position", position_ids)
    selected = next((item for item in positions if item.position.position_id == selected_id), None)
    if not selected:
        st.write("Position not found.")
        return

    cols = st.columns(3)
    cols[0].metric("Spread Value", f"{selected.spread_value:.2f}" if selected.spread_value else "N/A")
    cols[1].metric("Current P/L", f"${selected.current_pl:,.2f}" if selected.current_pl else "N/A")
    cols[2].metric("Exit Action", selected.exit_action)

    st.markdown("#### Exit Details")
    st.json(selected.exit_details)


def main() -> None:
    st.set_page_config(page_title="Credit Spread System", layout="wide")
    _apply_theme()
    _build_header()

    data_service, alpaca = _load_services()

    _render_summary(data_service)
    _render_iv_rank(alpaca)
    _render_market_context(data_service)
    positions = _render_positions_table(data_service)
    _render_position_detail(positions)


if __name__ == "__main__":
    main()
