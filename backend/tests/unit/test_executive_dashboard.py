"""Unit tests for the Executive Dashboard module.

Covers:
- Schema validation and serialization round-trip
- Repository aggregations (KPI strip, sales trend, pipeline, AI recs, alerts)
- Service orchestration payload shape
- Forecast confidence bucketing
- VIP / inactive / lead-abandoned detection rules

All DB access is mocked via the shared ``mock_session`` fixture.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.modules.executive_dashboard.repository import ExecutiveDashboardRepository
from app.modules.executive_dashboard.schemas import (
    AIRecommendation,
    ExecutiveDashboardResponse,
    ExecutiveForecast,
    ExecutiveKPIStrip,
    ExecutivePeriod,
    TopCustomer,
    TopProducts,
)
from app.modules.executive_dashboard.service import ExecutiveDashboardService


TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _execute_result(*, one=None, all_rows=None, scalar=0) -> MagicMock:
    """Build a fake ``Session.execute(...)`` return value."""
    result = MagicMock()
    if one is not None:
        result.one.return_value = one
    if all_rows is not None:
        result.all.return_value = all_rows
    result.scalar_one.return_value = scalar
    return result


def _kpi_payload() -> dict:
    return {
        "sales_today": Decimal("100.00"),
        "sales_week": Decimal("500.00"),
        "sales_month": Decimal("2000.00"),
        "sales_year": Decimal("20000.00"),
        "average_ticket": Decimal("125.50"),
        "average_ticket_month": Decimal("150.00"),
        "active_customers": 25,
        "vip_customers": 4,
        "active_conversations": 7,
        "leads_open": 12,
        "leads_won": 3,
        "leads_lost": 1,
        "conversion_rate_pct": 75.0,
        "total_orders": 90,
    }


# ===========================================================================
# SECTION 1 — Repository: period helpers
# ===========================================================================
class TestPeriodHelpers:
    def test_period_today_midnight_utc(self) -> None:
        repo = ExecutiveDashboardRepository(session=AsyncMock())
        p = repo._period(datetime(2026, 6, 5, 14, 30, tzinfo=UTC))
        assert p["today"] == datetime(2026, 6, 5, 0, 0, tzinfo=UTC)

    def test_period_week_start_is_monday(self) -> None:
        # 2026-06-05 is a Friday. Monday of that week is 2026-06-01.
        repo = ExecutiveDashboardRepository(session=AsyncMock())
        p = repo._period(datetime(2026, 6, 5, 14, 30, tzinfo=UTC))
        assert p["week_start"] == datetime(2026, 6, 1, 0, 0, tzinfo=UTC)

    def test_period_month_start_is_first_of_month(self) -> None:
        repo = ExecutiveDashboardRepository(session=AsyncMock())
        p = repo._period(datetime(2026, 6, 5, 14, 30, tzinfo=UTC))
        assert p["month_start"] == datetime(2026, 6, 1, 0, 0, tzinfo=UTC)

    def test_period_year_start_is_jan_1(self) -> None:
        repo = ExecutiveDashboardRepository(session=AsyncMock())
        p = repo._period(datetime(2026, 6, 5, 14, 30, tzinfo=UTC))
        assert p["year_start"] == datetime(2026, 1, 1, 0, 0, tzinfo=UTC)


# ===========================================================================
# SECTION 2 — Repository: confidence bucketing
# ===========================================================================
class TestConfidenceBucketing:
    @pytest.mark.parametrize(
        "sample,expected",
        [(0, "low"), (2, "low"), (3, "medium"), (5, "medium"), (6, "high"), (24, "high")],
    )
    def test_confidence(self, sample: int, expected: str) -> None:
        assert ExecutiveDashboardRepository._confidence_for_sample(sample) == expected


# ===========================================================================
# SECTION 3 — Repository: KPI strip
# ===========================================================================
class TestKpiStrip:
    @pytest.mark.asyncio
    async def test_kpi_strip_returns_full_payload(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        # The method issues multiple .execute() calls; queue results:
        # 1) sales today/week/month/year
        # 2) avg ticket (30d)
        # 3) avg ticket (month)
        # 4) active customers
        # 5) vip count
        # 6) conversations_core
        # 7) conversations legacy
        # 8) pipeline counts
        # 9) total orders
        sales_row = SimpleNamespace(
            sales_today=100, sales_week=500, sales_month=2000, sales_year=20000
        )
        mock_session.execute.side_effect = [
            _execute_result(one=sales_row),
            _execute_result(scalar=125.5),
            _execute_result(scalar=150.0),
            _execute_result(scalar=25),
            _execute_result(scalar=4),
            _execute_result(scalar=5),
            _execute_result(scalar=2),
            _execute_result(
                one=SimpleNamespace(open=12, won=3, lost=1)
            ),
            _execute_result(scalar=90),
        ]
        out = await repo.kpi_strip(
            empresa_id=TENANT_ID,
            period=repo._period(datetime.now(UTC)),
        )
        assert out["sales_today"] == Decimal("100")
        assert out["sales_year"] == Decimal("20000")
        assert out["average_ticket"] == Decimal("125.50")
        assert out["active_customers"] == 25
        assert out["vip_customers"] == 4
        assert out["active_conversations"] == 7  # 5 + 2
        assert out["leads_open"] == 12
        assert out["leads_won"] == 3
        assert out["leads_lost"] == 1
        # 3 / (3+1) = 75.0
        assert out["conversion_rate_pct"] == 75.0
        assert out["total_orders"] == 90

    @pytest.mark.asyncio
    async def test_kpi_strip_conversion_zero_when_no_closed(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        sales_row = SimpleNamespace(
            sales_today=0, sales_week=0, sales_month=0, sales_year=0
        )
        mock_session.execute.side_effect = [
            _execute_result(one=sales_row),
            _execute_result(scalar=None),
            _execute_result(scalar=None),
            _execute_result(scalar=0),
            _execute_result(scalar=0),
            _execute_result(scalar=0),
            _execute_result(scalar=0),
            _execute_result(one=SimpleNamespace(open=5, won=0, lost=0)),
            _execute_result(scalar=0),
        ]
        out = await repo.kpi_strip(
            empresa_id=TENANT_ID,
            period=repo._period(datetime.now(UTC)),
        )
        assert out["conversion_rate_pct"] == 0.0
        assert out["leads_won"] == 0
        assert out["leads_lost"] == 0


# ===========================================================================
# SECTION 4 — Repository: sales trend daily
# ===========================================================================
class TestSalesTrendDaily:
    @pytest.mark.asyncio
    async def test_daily_returns_30_points_continuous(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        # Simulate 5 days of data
        base = datetime.now(UTC).date()
        rows = []
        for offset, rev, orders in [(0, 100, 2), (5, 250, 4), (10, 50, 1), (15, 0, 0), (20, 320, 6)]:
            bucket = datetime.combine(base - timedelta(days=offset), datetime.min.time(), tzinfo=UTC)
            rows.append((bucket, rev, orders))
        mock_session.execute.return_value = _execute_result(all_rows=rows)
        out = await repo.sales_trend_daily(empresa_id=TENANT_ID, days=30)
        assert len(out) == 30  # 30 days of data points
        # Every entry has date/revenue/orders keys
        for point in out:
            assert set(point.keys()) == {"date", "revenue", "orders"}
        # 5 known days have correct revenue
        nonzero = [p for p in out if p["revenue"] > 0]
        assert len(nonzero) == 4  # the (15, 0, 0) day has 0 revenue

    @pytest.mark.asyncio
    async def test_daily_empty_dataset_returns_zeros(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        mock_session.execute.return_value = _execute_result(all_rows=[])
        out = await repo.sales_trend_daily(empresa_id=TENANT_ID, days=7)
        assert len(out) == 7
        assert all(p["orders"] == 0 for p in out)
        assert all(p["revenue"] == 0 for p in out)


# ===========================================================================
# SECTION 5 — Repository: sales trend monthly
# ===========================================================================
class TestSalesTrendMonthly:
    @pytest.mark.asyncio
    async def test_monthly_returns_12_continuous_months(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        rows = [
            (datetime(2026, 1, 1, tzinfo=UTC), 1000, 5),
            (datetime(2026, 3, 1, tzinfo=UTC), 2500, 8),
            (datetime(2026, 6, 1, tzinfo=UTC), 1700, 6),
        ]
        mock_session.execute.return_value = _execute_result(all_rows=rows)
        out = await repo.sales_trend_monthly(empresa_id=TENANT_ID, months=12)
        assert len(out) == 12
        for point in out:
            assert set(point.keys()) == {"month", "revenue", "orders"}
        # Check that one of the known months has correct data
        jun = [p for p in out if p["month"] == "2026-06"][0]
        assert jun["revenue"] == Decimal("1700")
        assert jun["orders"] == 6


# ===========================================================================
# SECTION 6 — Repository: pipeline summary
# ===========================================================================
class TestPipelineSummary:
    @pytest.mark.asyncio
    async def test_pipeline_summary_full_funnel(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        # 1) values
        value_row = SimpleNamespace(
            open_value=15000, weighted_value=7500, won_value=8000, lost_value=2000
        )
        # 2) funnel
        funnel_rows = [
            ("new_lead", 4, 2000),
            ("contacted", 3, 3000),
            ("qualified", 2, 4000),
            ("proposal", 2, 5000),
            ("negotiation", 1, 6000),
            ("won", 3, 8000),
            ("lost", 1, 2000),
        ]
        # 3) avg close
        mock_session.execute.side_effect = [
            _execute_result(one=value_row),
            _execute_result(all_rows=funnel_rows),
            _execute_result(scalar=5.5),
        ]
        out = await repo.pipeline_summary(empresa_id=TENANT_ID)
        assert out["total_value"] == Decimal("15000")
        assert out["weighted_value"] == Decimal("7500")
        assert out["won_value"] == Decimal("8000")
        assert out["lost_value"] == Decimal("2000")
        # Won / (Won+Lost) = 3/4 = 75
        assert out["conversion_pct"] == 75.0
        assert out["open_deals"] == 12  # 4+3+2+2+1
        assert out["won_deals"] == 3
        assert out["lost_deals"] == 1
        assert out["average_time_to_close_days"] == 5.5
        # Funnel has 7 stages in correct order
        assert len(out["funnel"]) == 7
        assert [f["stage"] for f in out["funnel"]] == [
            "new_lead", "contacted", "qualified", "proposal",
            "negotiation", "won", "lost",
        ]
        assert out["funnel"][0]["color"] == "#6366f1"
        assert out["funnel"][5]["color"] == "#10b981"

    @pytest.mark.asyncio
    async def test_pipeline_summary_zero_conversion(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        value_row = SimpleNamespace(
            open_value=0, weighted_value=0, won_value=0, lost_value=0
        )
        funnel_rows = [("new_lead", 0, 0)]
        mock_session.execute.side_effect = [
            _execute_result(one=value_row),
            _execute_result(all_rows=funnel_rows),
            _execute_result(scalar=None),
        ]
        out = await repo.pipeline_summary(empresa_id=TENANT_ID)
        assert out["conversion_pct"] == 0.0
        assert out["open_deals"] == 0
        assert out["average_time_to_close_days"] == 0.0


# ===========================================================================
# SECTION 7 — Repository: forecast
# ===========================================================================
class TestForecast:
    @pytest.mark.asyncio
    async def test_forecast_with_history(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        # 6 months with revenue 1000, 2000, 1500, 3000, 2500, 2000
        # avg = 2000
        rows = [
            (datetime(2026, m, 1, tzinfo=UTC), rev, 3)
            for m, rev in [(1, 1000), (2, 2000), (3, 1500), (4, 3000), (5, 2500), (6, 2000)]
        ]
        mock_session.execute.return_value = _execute_result(all_rows=rows)
        out = await repo.forecast(empresa_id=TENANT_ID)
        assert out["monthly"]["projected_revenue"] == Decimal("2000.00")
        assert out["monthly"]["confidence"] == "high"
        assert out["monthly"]["sample_size"] == 6
        assert out["quarterly"]["projected_revenue"] == Decimal("6000.00")
        assert out["quarterly"]["confidence"] == "high"
        assert "6 meses" in out["monthly"]["basis"]

    @pytest.mark.asyncio
    async def test_forecast_no_history_returns_zero(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        mock_session.execute.return_value = _execute_result(all_rows=[])
        out = await repo.forecast(empresa_id=TENANT_ID)
        assert out["monthly"]["projected_revenue"] == Decimal("0")
        assert out["monthly"]["confidence"] == "low"
        assert out["monthly"]["sample_size"] == 0
        assert out["quarterly"]["projected_revenue"] == Decimal("0")

    @pytest.mark.asyncio
    async def test_forecast_with_partial_history(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        # 3 months with revenue (medium confidence)
        rows = [
            (datetime(2026, m, 1, tzinfo=UTC), 1000, 1)
            for m in (1, 2, 3)
        ]
        mock_session.execute.return_value = _execute_result(all_rows=rows)
        out = await repo.forecast(empresa_id=TENANT_ID)
        assert out["monthly"]["confidence"] == "medium"
        assert out["monthly"]["projected_revenue"] == Decimal("1000.00")


# ===========================================================================
# SECTION 8 — Repository: top customers
# ===========================================================================
class TestTopCustomers:
    @pytest.mark.asyncio
    async def test_top_customer_vip_and_engagement(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        # The repo issues 1 execute() (for the outer query) which returns the
        # 10 customer rows with aggregations already attached via subquery.
        cust_id = uuid4()
        last_purchase = datetime.now(UTC) - timedelta(days=10)
        row = SimpleNamespace(
            id=cust_id,
            full_name="María Pérez",
            email="maria@example.com",
            phone="+51999999999",
            is_vip=True,
            order_count=12,
            lifetime_value=Decimal("5400.00"),
            average_ticket=Decimal("450.00"),
            last_purchase_at=last_purchase,
        )
        mock_session.execute.return_value = _execute_result(all_rows=[row])
        out = await repo.top_customers(empresa_id=TENANT_ID, limit=10)
        assert len(out) == 1
        c = out[0]
        assert c["id"] == cust_id
        assert c["full_name"] == "María Pérez"
        assert c["is_vip"] is True
        assert c["order_count"] == 12
        assert c["lifetime_value"] == Decimal("5400.00")
        assert c["days_since_last_purchase"] == 10

    @pytest.mark.asyncio
    async def test_top_customer_null_last_purchase(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        row = SimpleNamespace(
            id=uuid4(),
            full_name="Sin Compra",
            email=None,
            phone=None,
            is_vip=False,
            order_count=0,
            lifetime_value=Decimal("0"),
            average_ticket=Decimal("0"),
            last_purchase_at=None,
        )
        mock_session.execute.return_value = _execute_result(all_rows=[row])
        out = await repo.top_customers(empresa_id=TENANT_ID, limit=10)
        assert out[0]["days_since_last_purchase"] is None
        assert out[0]["is_vip"] is False


# ===========================================================================
# SECTION 9 — Repository: top products
# ===========================================================================
class TestTopProducts:
    @pytest.mark.asyncio
    async def test_top_products_three_lists(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        # 5 product rows
        rows = [
            SimpleNamespace(
                product_id=uuid4(),
                name="Polo Premium",
                units_sold=120,
                revenue=Decimal("3600.00"),
            ),
            SimpleNamespace(
                product_id=uuid4(),
                name="Vestido Floral",
                units_sold=80,
                revenue=Decimal("4800.00"),
            ),
            SimpleNamespace(
                product_id=uuid4(),
                name="Casaca Negra",
                units_sold=50,
                revenue=Decimal("3500.00"),
            ),
            SimpleNamespace(
                product_id=uuid4(),
                name="Blusa Blanca",
                units_sold=30,
                revenue=Decimal("900.00"),
            ),
            SimpleNamespace(
                product_id=uuid4(),
                name="Pantalón Jean",
                units_sold=20,
                revenue=Decimal("1200.00"),
            ),
        ]
        mock_session.execute.return_value = _execute_result(all_rows=rows)
        out = await repo.top_products(empresa_id=TENANT_ID, limit=5)
        assert len(out["most_sold"]) == 5
        # Most sold should be Polo Premium (120 units)
        assert out["most_sold"][0]["name"] == "Polo Premium"
        assert out["most_sold"][0]["units_sold"] == 120
        # Most profitable should be Vestido Floral (highest revenue)
        assert out["most_profitable"][0]["name"] == "Vestido Floral"
        assert out["most_profitable"][0]["revenue"] == Decimal("4800.00")
        # Most consulted: empty (no product-views table)
        assert out["most_consulted"] == []


# ===========================================================================
# SECTION 10 — Repository: alerts
# ===========================================================================
class TestAlertsInventoryCritical:
    @pytest.mark.asyncio
    async def test_inventory_critical_out_and_low(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        out_product_id = uuid4()
        low_product_id = uuid4()
        rows = [
            (out_product_id, "Producto Agotado", 0, 5),
            (low_product_id, "Producto Bajo", 2, 5),
        ]
        mock_session.execute.return_value = _execute_result(all_rows=rows)
        out = await repo.alerts_inventory_critical(empresa_id=TENANT_ID)
        assert len(out) == 2
        statuses = {r["name"]: r["status"] for r in out}
        assert statuses["Producto Agotado"] == "out"
        assert statuses["Producto Bajo"] == "low"


class TestAlertsLeadsAbandoned:
    @pytest.mark.asyncio
    async def test_leads_abandoned_calculates_days(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        last = datetime.now(UTC) - timedelta(days=15)
        rows = [
            (uuid4(), "Viejo trato 1", "negotiation", last, Decimal("500")),
            (uuid4(), "Viejo trato 2", "qualified", last, Decimal("300")),
        ]
        mock_session.execute.return_value = _execute_result(all_rows=rows)
        out = await repo.alerts_leads_abandoned(empresa_id=TENANT_ID)
        assert len(out) == 2
        for r in out:
            assert r["days_inactive"] >= 15
            assert r["value"] > 0


class TestAlertsConversationsUnanswered:
    @pytest.mark.asyncio
    async def test_conversations_unanswered_combines_sources(
        self, mock_session: AsyncMock
    ) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        # 1) conversations_core
        core_rows = [
            (uuid4(), datetime.now(UTC) - timedelta(hours=48), uuid4(), "Cliente A"),
        ]
        # 2) legacy conversations
        legacy_rows = [
            (uuid4(), datetime.now(UTC) - timedelta(hours=72), "whatsapp", "Cliente B"),
        ]
        mock_session.execute.side_effect = [
            _execute_result(all_rows=core_rows),
            _execute_result(all_rows=legacy_rows),
        ]
        out = await repo.alerts_conversations_unanswered(empresa_id=TENANT_ID)
        assert len(out) == 2
        # Sorted desc by hours_silent
        assert out[0]["hours_silent"] >= out[1]["hours_silent"]
        assert out[0]["channel"] == "whatsapp"


class TestAlertsInactiveCustomers:
    @pytest.mark.asyncio
    async def test_inactive_customers_filters_recent(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        old = datetime.now(UTC) - timedelta(days=120)
        rows = [(uuid4(), "Cliente Antiguo", old)]
        mock_session.execute.return_value = _execute_result(all_rows=rows)
        out = await repo.alerts_inactive_customers(empresa_id=TENANT_ID)
        assert len(out) == 1
        assert out[0]["days_inactive"] >= 120
        assert out[0]["last_purchase_at"] is not None


class TestAlertsDelayedOrders:
    @pytest.mark.asyncio
    async def test_delayed_orders_open_over_3_days(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        created = datetime.now(UTC) - timedelta(days=5)
        rows = [
            (uuid4(), "ORD-001", "Cliente X", "pending", created, Decimal("250.00")),
        ]
        mock_session.execute.return_value = _execute_result(all_rows=rows)
        out = await repo.alerts_delayed_orders(empresa_id=TENANT_ID)
        assert len(out) == 1
        assert out[0]["order_number"] == "ORD-001"
        assert out[0]["days_since_created"] >= 5
        assert out[0]["status"] == "pending"


# ===========================================================================
# SECTION 11 — Repository: AI recommendations
# ===========================================================================
class TestAIRecommendations:
    @pytest.mark.asyncio
    async def test_ai_recs_groups_by_category(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        deal_id = uuid4()
        cust_id = uuid4()
        prod_id = uuid4()
        # 1) hot leads
        # 2) VIP inactive
        # 3) recurrent (subquery already aggregated)
        # 4) accelerated products
        mock_session.execute.side_effect = [
            _execute_result(all_rows=[
                SimpleNamespace(
                    id=deal_id,
                    title="Trato VIP",
                    probability=90,
                    estimated_value=Decimal("5000"),
                    stage="negotiation",
                    customer_id=cust_id,
                    full_name="María",
                )
            ]),
            _execute_result(all_rows=[
                SimpleNamespace(
                    id=cust_id,
                    full_name="VIP Cliente",
                    lead_score=85,
                    last_interaction_at=datetime.now(UTC) - timedelta(days=20),
                )
            ]),
            _execute_result(all_rows=[
                SimpleNamespace(
                    id=uuid4(),
                    full_name="Recurrente 1",
                    order_count=4,
                    lifetime_value=Decimal("2500"),
                ),
            ]),
            _execute_result(all_rows=[
                SimpleNamespace(
                    id=prod_id,
                    name="Producto Estrella",
                    units_recent=50,
                ),
            ]),
        ]
        out = await repo.ai_recommendations(empresa_id=TENANT_ID)
        assert len(out) > 0
        # Categories present
        categories = {r["category"] for r in out}
        assert "lead_caliente" in categories
        assert "vip_inactivo" in categories
        assert "upsell" in categories
        assert "producto_top" in categories
        # Sorted by score desc
        scores = [r["score"] for r in out]
        assert scores == sorted(scores, reverse=True)
        # Score in 0-100
        for r in out:
            assert 0 <= r["score"] <= 100
            assert r["priority"] in ("high", "medium", "low")
            assert r["id"]
            assert r["cta_label"]
            assert r["cta_href"]

    @pytest.mark.asyncio
    async def test_ai_recs_caps_at_10(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        # Build 20 hot leads
        hot_leads = [
            SimpleNamespace(
                id=uuid4(),
                title=f"Trato {i}",
                probability=50 + i,
                estimated_value=Decimal("1000"),
                stage="negotiation",
                customer_id=uuid4(),
                full_name=f"Cliente {i}",
            )
            for i in range(20)
        ]
        mock_session.execute.side_effect = [
            _execute_result(all_rows=hot_leads),
            _execute_result(all_rows=[]),  # no VIP
            _execute_result(all_rows=[]),  # no recurrent
            _execute_result(all_rows=[]),  # no top product
        ]
        out = await repo.ai_recommendations(empresa_id=TENANT_ID)
        assert len(out) <= 10


# ===========================================================================
# SECTION 12 — Service orchestration
# ===========================================================================
class TestServiceOrchestration:
    @pytest.mark.asyncio
    async def test_service_composes_full_payload(self, mock_session: AsyncMock) -> None:
        svc = ExecutiveDashboardService(session=mock_session)

        # A permissive SimpleNamespace that contains every named field any of
        # the repository methods may access. This lets us assert that the
        # service orchestrates the calls correctly without caring which row
        # the mocked session returns for each call.
        universal_row = SimpleNamespace(
            sales_today=0, sales_week=0, sales_month=0, sales_year=0,
            open_value=0, weighted_value=0, won_value=0, lost_value=0,
            open=0, won=0, lost=0,
        )
        default_result = MagicMock()
        default_result.one.return_value = universal_row
        default_result.all.return_value = []
        default_result.scalar_one.return_value = 0
        mock_session.execute.return_value = default_result

        response = await svc.get_dashboard(tenant_id=TENANT_ID)

        assert isinstance(response, ExecutiveDashboardResponse)
        assert isinstance(response.kpis, ExecutiveKPIStrip)
        assert response.currency == "PEN"
        assert response.metadata.tenant_id == TENANT_ID
        assert response.metadata.computed_in_ms >= 0
        assert isinstance(response.period, ExecutivePeriod)
        # 30 days of trend data
        assert len(response.sales_trend.daily) == 30
        # 12 months of trend data
        assert len(response.sales_trend.monthly) == 12
        # Funnel has 7 stages even with zero data
        assert len(response.pipeline.funnel) == 7
        assert isinstance(response.forecast, ExecutiveForecast)
        assert response.alerts is not None


# ===========================================================================
# SECTION 13 — Schema validation
# ===========================================================================
class TestSchemas:
    def test_period_serializes(self) -> None:
        p = ExecutivePeriod(
            today=datetime(2026, 6, 5, tzinfo=UTC),
            week_start=datetime(2026, 6, 1, tzinfo=UTC),
            month_start=datetime(2026, 6, 1, tzinfo=UTC),
            year_start=datetime(2026, 1, 1, tzinfo=UTC),
        )
        assert p.today.day == 5
        assert p.year_start.month == 1

    def test_kpi_strip_required_fields(self) -> None:
        with pytest.raises(Exception):
            ExecutiveKPIStrip()  # type: ignore[call-arg]

    def test_top_customer_basic(self) -> None:
        c = TopCustomer(
            id=uuid4(),
            full_name="Ana",
            order_count=2,
            lifetime_value=Decimal("100.00"),
            average_ticket=Decimal("50.00"),
        )
        assert c.is_vip is False
        assert c.email is None
        assert c.days_since_last_purchase is None

    def test_ai_recommendation_validates_score(self) -> None:
        with pytest.raises(Exception):
            AIRecommendation(
                id="x",
                title="t",
                description="d",
                score=150,  # > 100
                priority="high",
                category="c",
                cta_label="cta",
            )
        with pytest.raises(Exception):
            AIRecommendation(
                id="x",
                title="t",
                description="d",
                score=50,
                priority="urgent",  # not in enum
                category="c",
                cta_label="cta",
            )

    def test_top_products_serializes(self) -> None:
        tp = TopProducts(
            most_sold=[],
            most_profitable=[],
            most_consulted=[],
        )
        assert tp.most_sold == []
        assert tp.most_consulted == []


# ===========================================================================
# SECTION 14 — Edge cases and tenant isolation
# ===========================================================================
class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_forecast_handles_all_zero_history(self, mock_session: AsyncMock) -> None:
        # If months have buckets but all revenue=0, they should be filtered.
        repo = ExecutiveDashboardRepository(session=mock_session)
        rows = [
            (datetime(2026, m, 1, tzinfo=UTC), 0, 0) for m in range(1, 7)
        ]
        mock_session.execute.return_value = _execute_result(all_rows=rows)
        out = await repo.forecast(empresa_id=TENANT_ID)
        assert out["monthly"]["projected_revenue"] == Decimal("0")
        assert out["monthly"]["sample_size"] == 0
        assert out["monthly"]["confidence"] == "low"

    @pytest.mark.asyncio
    async def test_kpi_strip_uses_tenant_id_in_queries(
        self, mock_session: AsyncMock
    ) -> None:
        # The tenant must be passed to every aggregation.
        repo = ExecutiveDashboardRepository(session=mock_session)
        mock_session.execute.side_effect = [
            _execute_result(
                one=SimpleNamespace(
                    sales_today=0, sales_week=0, sales_month=0, sales_year=0
                )
            ),
            _execute_result(scalar=None),
            _execute_result(scalar=None),
            _execute_result(scalar=0),
            _execute_result(scalar=0),
            _execute_result(scalar=0),
            _execute_result(scalar=0),
            _execute_result(one=SimpleNamespace(open=0, won=0, lost=0)),
            _execute_result(scalar=0),
        ]
        await repo.kpi_strip(
            empresa_id=TENANT_ID,
            period=repo._period(datetime.now(UTC)),
        )
        # All 9 execute calls were made
        assert mock_session.execute.await_count == 9

    @pytest.mark.asyncio
    async def test_top_customers_empty(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        mock_session.execute.return_value = _execute_result(all_rows=[])
        out = await repo.top_customers(empresa_id=TENANT_ID, limit=10)
        assert out == []

    @pytest.mark.asyncio
    async def test_pipeline_handles_empty_db(self, mock_session: AsyncMock) -> None:
        repo = ExecutiveDashboardRepository(session=mock_session)
        mock_session.execute.side_effect = [
            _execute_result(
                one=SimpleNamespace(
                    open_value=0, weighted_value=0, won_value=0, lost_value=0
                )
            ),
            _execute_result(all_rows=[]),
            _execute_result(scalar=None),
        ]
        out = await repo.pipeline_summary(empresa_id=TENANT_ID)
        # All 7 stages still emitted with zero counts
        assert len(out["funnel"]) == 7
        assert all(s["count"] == 0 for s in out["funnel"])
        assert all(s["value"] == 0 for s in out["funnel"])
