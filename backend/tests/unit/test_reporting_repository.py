"""Unit tests for the Reporting module — repository aggregations.

Covers every aggregation method on ``ReportingRepository``. Uses a
fully-mocked ``AsyncSession`` and never touches a real database.
"""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID


from app.modules.reporting.repository import ReportingRepository


REPORTING_TENANT = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")


def _result_row(**kwargs):
    """Create a MagicMock that mimics a SQLAlchemy Row."""
    return SimpleNamespace(**kwargs)


def _scalar_result(value):
    """Build a fake execute() result that returns a single scalar."""
    result = MagicMock()
    result.scalar_one = MagicMock(return_value=value)
    result.scalar = MagicMock(return_value=value)
    result.one = MagicMock(return_value=SimpleNamespace(**{"_asdict": lambda self: {}}))
    return result


def _one_result(row: SimpleNamespace) -> MagicMock:
    """Build a fake execute() result that returns a single row from .one()."""
    result = MagicMock()
    result.one = MagicMock(return_value=row)
    result.scalar_one = MagicMock(return_value=0)
    result.all = MagicMock(return_value=[])
    return result


def _rows_result(rows):
    """Build a fake execute() result that returns .all() = rows."""
    result = MagicMock()
    result.all = MagicMock(return_value=rows)
    result.scalar_one = MagicMock(return_value=0)
    result.one = MagicMock(return_value=SimpleNamespace(**{"_asdict": lambda self: {}}))
    result.scalars = MagicMock()
    result.scalars.return_value.all = MagicMock(return_value=rows)
    return result


def _make_session() -> AsyncMock:
    session = AsyncMock()
    session.execute = AsyncMock()
    return session


class TestReportingRepositoryUtils:
    def test_now_is_utc_aware(self) -> None:
        n = ReportingRepository._now()
        assert n.tzinfo is not None
        assert n.tzinfo.utcoffset(n).total_seconds() == 0

    def test_period_returns_four_keys(self) -> None:
        now = datetime(2026, 6, 6, 10, 0, 0, tzinfo=UTC)
        period = ReportingRepository._period(now)
        assert set(period.keys()) == {"today", "week_start", "month_start", "year_start"}
        assert period["year_start"].year == 2026
        assert period["year_start"].month == 1
        assert period["month_start"].month == 6
        assert period["today"].hour == 0
        assert period["today"].minute == 0

    def test_month_key_format(self) -> None:
        dt = datetime(2026, 3, 15, tzinfo=UTC)
        assert ReportingRepository._month_key(dt) == "2026-03"

    def test_period_week_starts_on_monday(self) -> None:
        # 2026-06-06 is a Saturday; week_start should be Monday 2026-06-01
        now = datetime(2026, 6, 6, 12, 0, 0, tzinfo=UTC)
        period = ReportingRepository._period(now)
        assert period["week_start"].weekday() == 0
        assert period["week_start"].day == 1


class TestSalesKpis:
    def test_sales_kpis_returns_decimal_fields(self) -> None:
        session = _make_session()
        # First call: sales aggregation row
        # Subsequent calls: ticket_30, ticket_month
        # Plus count_since
        sales_row = SimpleNamespace(
            sales_today=Decimal("100"),
            sales_week=Decimal("500"),
            sales_month=Decimal("2000"),
            sales_year=Decimal("20000"),
            orders_today=3,
            orders_week=10,
            orders_month=30,
            total_orders=120,
        )
        ticket_row = MagicMock()
        ticket_row.scalar_one = MagicMock(return_value=Decimal("150"))
        session.execute.side_effect = [
            _one_result(sales_row),
            ticket_row,
            ticket_row,
        ]
        repo = ReportingRepository(session)
        period = repo._period(repo._now())
        result = _run(repo.sales_kpis(empresa_id=REPORTING_TENANT, period=period))
        assert result["sales_today"] == Decimal("100")
        assert result["sales_month"] == Decimal("2000")
        assert result["average_ticket"] == Decimal("150.00")
        assert result["orders_today"] == 3
        assert result["total_orders"] == 120


class TestDailyAndMonthlySales:
    def test_daily_sales_groups_by_day(self) -> None:
        session = _make_session()
        # Use a fixed "now" so the backfill window is deterministic.
        # today=2026-06-06 -> start=2026-06-01, end=2026-06-07, range=6 buckets
        rows = [
            (datetime(2026, 6, 1, 12, 0, tzinfo=UTC), Decimal("100"), 1),
            (datetime(2026, 6, 3, 12, 0, tzinfo=UTC), Decimal("250"), 2),
        ]
        session.execute.return_value = _rows_result(rows)
        repo = ReportingRepository(session)
        result = _run(repo.daily_sales(empresa_id=REPORTING_TENANT, days=7))
        # backfill: 7 days × 1 = 7 entries (start..end-1)
        assert len(result) == 7
        # Zero-bucket days are returned with 0
        assert all(d["orders"] >= 0 for d in result)
        # Both rows must be present in the result
        revenues = {d["date"]: d["revenue"] for d in result}
        assert revenues["2026-06-01"] == Decimal("100")
        assert revenues["2026-06-03"] == Decimal("250")

    def test_monthly_sales_returns_list(self) -> None:
        session = _make_session()
        rows = [
            (datetime(2026, 5, 1, tzinfo=UTC), Decimal("1000"), 5),
            (datetime(2026, 6, 1, tzinfo=UTC), Decimal("2000"), 8),
        ]
        session.execute.return_value = _rows_result(rows)
        repo = ReportingRepository(session)
        result = _run(repo.monthly_sales(empresa_id=REPORTING_TENANT, months=12))
        assert len(result) == 2
        assert result[0]["month"] == "2026-05"
        assert result[0]["revenue"] == Decimal("1000")


class TestCustomerKpis:
    def test_customer_kpis_returns_all_keys(self) -> None:
        session = _make_session()
        agg_row = SimpleNamespace(
            total=10,
            vip=2,
            recurrent=3,
            inactive=1,
            active=7,
            new=1,
            total_ltv=Decimal("5000"),
            total_orders=20,
        )
        session.execute.return_value = _one_result(agg_row)
        repo = ReportingRepository(session)
        result = _run(repo.customer_kpis(empresa_id=REPORTING_TENANT))
        assert result["total"] == 10
        assert result["vip"] == 2
        assert result["recurrent"] == 3
        assert result["inactive"] == 1
        assert result["active"] == 7
        assert result["average_lifetime_value"] == Decimal("500.00")
        assert result["average_orders_per_customer"] == Decimal("2.00")


class TestPipelineKpis:
    def test_pipeline_kpis_aggregates_by_stage(self) -> None:
        session = _make_session()
        # By-stage rows
        by_stage_rows = [
            ("new_lead", 3, Decimal("1500")),
            ("negotiation", 2, Decimal("4000")),
            ("won", 1, Decimal("2000")),
            ("lost", 1, Decimal("500")),
        ]
        result_obj = MagicMock()
        result_obj.all = MagicMock(return_value=by_stage_rows)
        weighted_result = MagicMock()
        weighted_result.scalar_one = MagicMock(return_value=Decimal("1800"))
        session.execute.side_effect = [result_obj, weighted_result]
        repo = ReportingRepository(session)
        result = _run(repo.pipeline_kpis(empresa_id=REPORTING_TENANT))
        assert result["open_deals"] == 5  # 3 new_lead + 2 negotiation
        assert result["won_deals"] == 1
        assert result["lost_deals"] == 1
        assert result["total_value"] == Decimal("5500")  # 1500 + 4000
        assert result["weighted_value"] == Decimal("1800")
        assert result["won_value"] == Decimal("2000")
        assert result["lost_value"] == Decimal("500")

    def test_pipeline_kpis_zero_closed_yields_zero_conversion(self) -> None:
        session = _make_session()
        by_stage_rows = [("new_lead", 5, Decimal("1000"))]
        result_obj = MagicMock()
        result_obj.all = MagicMock(return_value=by_stage_rows)
        weighted_result = MagicMock()
        weighted_result.scalar_one = MagicMock(return_value=Decimal("0"))
        session.execute.side_effect = [result_obj, weighted_result]
        repo = ReportingRepository(session)
        result = _run(repo.pipeline_kpis(empresa_id=REPORTING_TENANT))
        assert result["conversion_pct"] == 0.0


class TestPipelineFunnel:
    def test_pipeline_funnel_returns_seven_stages(self) -> None:
        session = _make_session()
        rows = [
            ("new_lead", 2, Decimal("100")),
            ("won", 1, Decimal("500")),
        ]
        session.execute.return_value = _rows_result(rows)
        repo = ReportingRepository(session)
        result = _run(repo.pipeline_funnel(empresa_id=REPORTING_TENANT))
        assert len(result) == 7
        stages = [r["stage"] for r in result]
        assert "won" in stages
        assert "lost" in stages
        # All zero for missing stages
        contact = next(r for r in result if r["stage"] == "contacted")
        assert contact["count"] == 0
        assert contact["value"] == Decimal("0")


class TestInventoryKpis:
    def test_inventory_kpis_aggregates(self) -> None:
        session = _make_session()
        # total_products count
        count_result = MagicMock()
        count_result.scalar_one = MagicMock(return_value=15)
        # main aggregation
        agg_result = MagicMock()
        agg_result.one = MagicMock(return_value=(
            Decimal("50000"),  # value
            100,              # units
            5,                # reserved
            2,                # out_of_stock
            3,                # low_stock
            10,               # normal_stock
        ))
        session.execute.side_effect = [count_result, agg_result]
        repo = ReportingRepository(session)
        result = _run(repo.inventory_kpis(empresa_id=REPORTING_TENANT))
        assert result["total_products"] == 15
        assert result["out_of_stock"] == 2
        assert result["low_stock"] == 3
        assert result["normal_stock"] == 10
        assert result["inventory_value"] == Decimal("50000")
        assert result["total_units"] == 100
        assert result["total_reserved_units"] == 5


class TestForecast:
    def test_forecast_with_no_history(self) -> None:
        session = _make_session()
        session.execute.return_value = _rows_result([])
        repo = ReportingRepository(session)
        result = _run(repo.forecast(empresa_id=REPORTING_TENANT))
        assert result["monthly"] == Decimal("0")
        assert result["quarterly"] == Decimal("0")
        assert result["confidence"] == "low"
        assert result["sample_size"] == 0

    def test_forecast_with_history(self) -> None:
        session = _make_session()
        rows = [
            (datetime(2026, 1, 15, tzinfo=UTC), Decimal("1000"), 5),
            (datetime(2026, 2, 15, tzinfo=UTC), Decimal("2000"), 7),
            (datetime(2026, 3, 15, tzinfo=UTC), Decimal("3000"), 10),
        ]
        session.execute.return_value = _rows_result(rows)
        repo = ReportingRepository(session)
        result = _run(repo.forecast(empresa_id=REPORTING_TENANT))
        assert result["monthly"] == Decimal("2000.00")
        assert result["quarterly"] == Decimal("6000.00")
        assert result["sample_size"] == 3
        assert result["confidence"] == "medium"


class TestLowestStock:
    def test_lowest_stock_classifies_status(self) -> None:
        session = _make_session()
        rows = [
            (UUID("11111111-1111-4111-8111-111111111111"), "Polo", 0, 5),
            (UUID("22222222-2222-4222-8222-222222222222"), "Vestido", 3, 5),
            (UUID("33333333-3333-4333-8333-333333333333"), "Casaca", 10, 5),
        ]
        session.execute.return_value = _rows_result(rows)
        repo = ReportingRepository(session)
        result = _run(repo.lowest_stock(empresa_id=REPORTING_TENANT, limit=5))
        statuses = {r["name"]: r["status"] for r in result}
        assert statuses["Polo"] == "agotado"
        assert statuses["Vestido"] == "stock_bajo"
        assert statuses["Casaca"] == "normal"


class TestTenantIsolation:
    """Verify the repository always passes empresa_id into the WHERE clause."""

    def test_sales_kpis_called_with_empresa_id(self) -> None:
        session = _make_session()
        sales_row = SimpleNamespace(
            sales_today=Decimal("0"),
            sales_week=Decimal("0"),
            sales_month=Decimal("0"),
            sales_year=Decimal("0"),
            orders_today=0,
            orders_week=0,
            orders_month=0,
            total_orders=0,
        )
        ticket = MagicMock()
        ticket.scalar_one = MagicMock(return_value=Decimal("0"))
        session.execute.side_effect = [
            _one_result(sales_row),
            ticket,
            ticket,
        ]
        repo = ReportingRepository(session)
        period = repo._period(repo._now())
        _run(repo.sales_kpis(empresa_id=REPORTING_TENANT, period=period))
        assert session.execute.await_count == 3
        assert session.execute.await_args is not None

    def test_customer_kpis_called_with_empresa_id(self) -> None:
        session = _make_session()
        agg_row = SimpleNamespace(
            total=0, vip=0, recurrent=0, inactive=0, active=0, new=0,
            total_ltv=Decimal("0"), total_orders=0,
        )
        session.execute.return_value = _one_result(agg_row)
        repo = ReportingRepository(session)
        _run(repo.customer_kpis(empresa_id=REPORTING_TENANT))
        assert session.execute.await_count == 1


def _run(coro):
    import asyncio
    return asyncio.run(coro)
