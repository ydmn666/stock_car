"""initial schema

Revision ID: 20260402_0001
Revises:
Create Date: 2026-04-02 15:30:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260402_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_history",
        sa.Column("stock_code", sa.String(length=20), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("open_price", sa.Float(), nullable=True),
        sa.Column("close_price", sa.Float(), nullable=True),
        sa.Column("high_price", sa.Float(), nullable=True),
        sa.Column("low_price", sa.Float(), nullable=True),
        sa.Column("volume", sa.Float(), nullable=True),
        sa.Column("turnover", sa.Float(), nullable=True),
        sa.Column("amplitude", sa.Float(), nullable=True),
        sa.Column("pct_change", sa.Float(), nullable=True),
        sa.Column("price_change", sa.Float(), nullable=True),
        sa.Column("turnover_rate", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("stock_code", "trade_date"),
    )

    op.create_table(
        "users",
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("username"),
    )

    op.create_table(
        "ai_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("stock_code", sa.String(length=20), nullable=False),
        sa.Column("date_range", sa.String(length=64), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("report_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stock_code", "date_range", name="uq_ai_reports_stock_date_range"),
    )
    op.create_index("ix_ai_reports_stock_code", "ai_reports", ["stock_code"])
    op.create_index("ix_ai_reports_date_range", "ai_reports", ["date_range"])
    op.create_index("ix_ai_reports_created_at", "ai_reports", ["created_at"])

    op.create_table(
        "stock_instruments",
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("market", sa.String(length=8), nullable=False, server_default="CN"),
        sa.Column("asset_type", sa.String(length=20), nullable=False, server_default="stock"),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("full_symbol", sa.String(length=32), nullable=False),
        sa.Column("exchange", sa.String(length=32), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="CNY"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("symbol"),
        sa.UniqueConstraint("full_symbol"),
    )
    op.create_index("ix_stock_instruments_market", "stock_instruments", ["market"])

    op.create_table(
        "news_cache",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("publisher", sa.String(length=64), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("matched_by", sa.String(length=32), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["symbol"], ["stock_instruments.symbol"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol", "title", "published_at", name="uq_news_cache_symbol_title_published_at"),
    )
    op.create_index("ix_news_cache_symbol", "news_cache", ["symbol"])
    op.create_index("ix_news_cache_published_at", "news_cache", ["published_at"])
    op.create_index("ix_news_cache_fetched_at", "news_cache", ["fetched_at"])

    op.create_table(
        "price_cache",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("adjusted", sa.String(length=12), nullable=False, server_default="qfq"),
        sa.Column("open_price", sa.Float(), nullable=True),
        sa.Column("close_price", sa.Float(), nullable=True),
        sa.Column("high_price", sa.Float(), nullable=True),
        sa.Column("low_price", sa.Float(), nullable=True),
        sa.Column("volume", sa.Float(), nullable=True),
        sa.Column("turnover", sa.Float(), nullable=True),
        sa.Column("amplitude", sa.Float(), nullable=True),
        sa.Column("pct_change", sa.Float(), nullable=True),
        sa.Column("price_change", sa.Float(), nullable=True),
        sa.Column("turnover_rate", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["symbol"], ["stock_instruments.symbol"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol", "trade_date", "adjusted", name="uq_price_cache_symbol_trade_date_adjusted"),
    )
    op.create_index("ix_price_cache_symbol", "price_cache", ["symbol"])
    op.create_index("ix_price_cache_trade_date", "price_cache", ["trade_date"])
    op.create_index("ix_price_cache_fetched_at", "price_cache", ["fetched_at"])

    op.create_table(
        "user_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("stock_name", sa.String(length=100), nullable=False),
        sa.Column("stock_code", sa.String(length=20), nullable=False),
        sa.Column("visit_time_str", sa.String(length=32), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["username"], ["users.username"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_history_username", "user_history", ["username"])

    op.create_table(
        "user_portfolios",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False, server_default="默认组合"),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("base_currency", sa.String(length=8), nullable=False, server_default="CNY"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["username"], ["users.username"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username", "name", name="uq_user_portfolios_username_name"),
    )
    op.create_index("ix_user_portfolios_username", "user_portfolios", ["username"])

    op.create_table(
        "investment_transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("stock_name", sa.String(length=100), nullable=False),
        sa.Column("trade_type", sa.String(length=16), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("fee", sa.Float(), nullable=False, server_default="0"),
        sa.Column("tax", sa.Float(), nullable=False, server_default="0"),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["user_portfolios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["symbol"], ["stock_instruments.symbol"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["username"], ["users.username"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_investment_transactions_portfolio_id", "investment_transactions", ["portfolio_id"])
    op.create_index("ix_investment_transactions_username", "investment_transactions", ["username"])
    op.create_index("ix_investment_transactions_symbol", "investment_transactions", ["symbol"])
    op.create_index("ix_investment_transactions_trade_date", "investment_transactions", ["trade_date"])

    op.create_table(
        "position_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False, server_default="0"),
        sa.Column("avg_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("invested_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("market_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("unrealized_pnl", sa.Float(), nullable=False, server_default="0"),
        sa.Column("unrealized_pnl_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["user_portfolios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["symbol"], ["stock_instruments.symbol"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["username"], ["users.username"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("portfolio_id", "symbol", "snapshot_date", name="uq_position_snapshots_portfolio_symbol_date"),
    )
    op.create_index("ix_position_snapshots_portfolio_id", "position_snapshots", ["portfolio_id"])
    op.create_index("ix_position_snapshots_username", "position_snapshots", ["username"])
    op.create_index("ix_position_snapshots_symbol", "position_snapshots", ["symbol"])
    op.create_index("ix_position_snapshots_snapshot_date", "position_snapshots", ["snapshot_date"])


def downgrade() -> None:
    op.drop_index("ix_position_snapshots_snapshot_date", table_name="position_snapshots")
    op.drop_index("ix_position_snapshots_symbol", table_name="position_snapshots")
    op.drop_index("ix_position_snapshots_username", table_name="position_snapshots")
    op.drop_index("ix_position_snapshots_portfolio_id", table_name="position_snapshots")
    op.drop_table("position_snapshots")

    op.drop_index("ix_investment_transactions_trade_date", table_name="investment_transactions")
    op.drop_index("ix_investment_transactions_symbol", table_name="investment_transactions")
    op.drop_index("ix_investment_transactions_username", table_name="investment_transactions")
    op.drop_index("ix_investment_transactions_portfolio_id", table_name="investment_transactions")
    op.drop_table("investment_transactions")

    op.drop_index("ix_user_portfolios_username", table_name="user_portfolios")
    op.drop_table("user_portfolios")

    op.drop_index("ix_user_history_username", table_name="user_history")
    op.drop_table("user_history")

    op.drop_index("ix_price_cache_fetched_at", table_name="price_cache")
    op.drop_index("ix_price_cache_trade_date", table_name="price_cache")
    op.drop_index("ix_price_cache_symbol", table_name="price_cache")
    op.drop_table("price_cache")

    op.drop_index("ix_news_cache_fetched_at", table_name="news_cache")
    op.drop_index("ix_news_cache_published_at", table_name="news_cache")
    op.drop_index("ix_news_cache_symbol", table_name="news_cache")
    op.drop_table("news_cache")

    op.drop_index("ix_stock_instruments_market", table_name="stock_instruments")
    op.drop_table("stock_instruments")

    op.drop_index("ix_ai_reports_created_at", table_name="ai_reports")
    op.drop_index("ix_ai_reports_date_range", table_name="ai_reports")
    op.drop_index("ix_ai_reports_stock_code", table_name="ai_reports")
    op.drop_table("ai_reports")

    op.drop_table("users")
    op.drop_table("stock_history")
