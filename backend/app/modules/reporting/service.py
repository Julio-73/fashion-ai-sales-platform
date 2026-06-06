"""Service layer for the Reporting module.

The service composes the ``ExecutiveReportData`` payload for each of the
five report types (executive, pipeline, crm, sales, inventory) by
querying ``ReportingRepository``. The generators consume the
pre-aggregated payload and never touch the database.

All methods are tenant-scoped via ``empresa_id`` taken from
``TenantContext``.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.reporting.repository import ReportingRepository
from app.modules.reporting.schemas import (
    ExecutiveReportData,
    ReportKPI,
    ReportMetadata,
    ReportSection,
    ReportTable,
)


# Section / sheet titles — kept short so the XLSX tab names are readable.
_SECTION_OVERVIEW = "Resumen Ejecutivo"
_SECTION_PIPELINE = "Pipeline"
_SECTION_SALES = "Ventas"
_SECTION_CUSTOMERS = "Clientes"
_SECTION_PRODUCTS = "Productos"
_SECTION_INVENTORY = "Inventario"
_SECTION_FORECAST = "Proyecciones"
_SECTION_ALERTS = "Alertas"

_DEFAULT_LIMIT = 5000
_TOP_LIMIT = 10


class ReportingService:
    """Orchestrates the per-tenant aggregations needed by the reports."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ReportingRepository(session)

    # ------------------------------------------------------------------ public
    async def build_executive_report(
        self, *, empresa_id: UUID
    ) -> ExecutiveReportData:
        period = self._repo._period(self._repo._now())
        emp = await self._repo.get_empresa(empresa_id=empresa_id)
        tenant_name = (emp or {}).get("nombre") or "Empresa"
        logo_url = (emp or {}).get("logo_url")
        sales = await self._repo.sales_kpis(empresa_id=empresa_id, period=period)
        customers = await self._repo.customer_kpis(empresa_id=empresa_id)
        pipeline = await self._repo.pipeline_kpis(empresa_id=empresa_id)
        inventory = await self._repo.inventory_kpis(empresa_id=empresa_id)
        forecast = await self._repo.forecast(empresa_id=empresa_id)
        top_customers = await self._repo.top_customers(
            empresa_id=empresa_id, limit=_TOP_LIMIT
        )
        top_products = await self._repo.top_products(
            empresa_id=empresa_id, limit=_TOP_LIMIT
        )
        recs = await self._repo.ai_recommendations(
            empresa_id=empresa_id, limit=5
        )
        inv_alerts = await self._repo.inventory_critical_alerts(
            empresa_id=empresa_id, limit=5
        )
        delayed = await self._repo.delayed_orders_alerts(
            empresa_id=empresa_id, limit=5
        )
        critical_alerts = inv_alerts + delayed

        kpis = self._build_executive_kpis(sales, customers, pipeline, inventory)
        sections = [
            self._build_sales_section(sales, period),
            self._build_pipeline_section(pipeline),
            self._build_customers_section(customers, top_customers),
            self._build_inventory_section(inventory, top_products),
            self._build_forecast_section(forecast, sales),
            self._build_alerts_section(inv_alerts, delayed),
        ]
        metadata = ReportMetadata(
            generated_at=self._repo._now(),
            tenant_id=empresa_id,
            tenant_name=tenant_name,
            tenant_logo_url=logo_url,
            period_label=self._build_period_label(period),
            currency="PEN",
        )
        return ExecutiveReportData(
            metadata=metadata,
            kpis=kpis,
            sections=sections,
            ai_recommendations=recs,
            critical_alerts=critical_alerts,
        )

    async def build_pipeline_report(
        self, *, empresa_id: UUID
    ) -> ExecutiveReportData:
        period = self._repo._period(self._repo._now())
        emp = await self._repo.get_empresa(empresa_id=empresa_id)
        tenant_name = (emp or {}).get("nombre") or "Empresa"
        logo_url = (emp or {}).get("logo_url")
        pipeline = await self._repo.pipeline_kpis(empresa_id=empresa_id)
        funnel = await self._repo.pipeline_funnel(empresa_id=empresa_id)
        deals = await self._repo.pipeline_deals_for_export(
            empresa_id=empresa_id, limit=_DEFAULT_LIMIT
        )
        kpis = self._build_pipeline_kpis(pipeline)
        sections = [
            self._build_pipeline_overview_section(pipeline),
            ReportSection(
                title="Embudo comercial",
                tables=[
                    ReportTable(
                        title="Distribución por etapa",
                        columns=["Etapa", "Deals", "Valor (S/)"],
                        rows=[
                            [
                                _stage_label(row["stage"]),
                                str(row["count"]),
                                _fmt_money(row["value"]),
                            ]
                            for row in funnel
                        ],
                        total_row=[
                            "Total",
                            str(sum(r["count"] for r in funnel)),
                            _fmt_money(sum(r["value"] for r in funnel)),
                        ],
                    )
                ],
            ),
            ReportSection(
                title="Listado de tratos",
                tables=[
                    ReportTable(
                        title=f"Detalle de los últimos {len(deals)} tratos",
                        columns=[
                            "Trato",
                            "Etapa",
                            "Cliente",
                            "Valor (S/)",
                            "Probabilidad",
                            "Creado",
                        ],
                        rows=[
                            [
                                _safe(d["title"], 40),
                                _stage_label(d["stage"]),
                                _safe(d["customer_name"], 30),
                                _fmt_money(d["value"]),
                                f"{d['probability']}%",
                                _fmt_date(d["created_at"]),
                            ]
                            for d in deals
                        ],
                    )
                ],
            ),
        ]
        return ExecutiveReportData(
            metadata=ReportMetadata(
                generated_at=self._repo._now(),
                tenant_id=empresa_id,
                tenant_name=tenant_name,
                tenant_logo_url=logo_url,
                period_label=self._build_period_label(period),
                currency="PEN",
            ),
            kpis=kpis,
            sections=sections,
        )

    async def build_crm_report(
        self, *, empresa_id: UUID
    ) -> ExecutiveReportData:
        period = self._repo._period(self._repo._now())
        emp = await self._repo.get_empresa(empresa_id=empresa_id)
        tenant_name = (emp or {}).get("nombre") or "Empresa"
        logo_url = (emp or {}).get("logo_url")
        customers = await self._repo.customer_kpis(empresa_id=empresa_id)
        rows = await self._repo.customers_for_export(
            empresa_id=empresa_id, limit=_DEFAULT_LIMIT
        )
        kpis = self._build_crm_kpis(customers)
        sections = [
            ReportSection(
                title="Cartera de clientes",
                tables=[
                    ReportTable(
                        title=f"Detalle de los {len(rows)} clientes principales",
                        columns=[
                            "Cliente",
                            "Email",
                            "Teléfono",
                            "Pedidos",
                            "LTV (S/)",
                            "Última compra",
                            "Categoría",
                        ],
                        rows=[
                            [
                                _safe(r["full_name"], 32),
                                _safe(r["email"] or "-", 28),
                                _safe(r["phone"] or "-", 16),
                                str(r["order_count"]),
                                _fmt_money(r["lifetime_value"]),
                                _fmt_date(r["last_purchase_at"]),
                                _customer_category(r),
                            ]
                            for r in rows
                        ],
                    )
                ],
            ),
        ]
        return ExecutiveReportData(
            metadata=ReportMetadata(
                generated_at=self._repo._now(),
                tenant_id=empresa_id,
                tenant_name=tenant_name,
                tenant_logo_url=logo_url,
                period_label=self._build_period_label(period),
                currency="PEN",
            ),
            kpis=kpis,
            sections=sections,
        )

    async def build_sales_report(
        self, *, empresa_id: UUID
    ) -> ExecutiveReportData:
        period = self._repo._period(self._repo._now())
        emp = await self._repo.get_empresa(empresa_id=empresa_id)
        tenant_name = (emp or {}).get("nombre") or "Empresa"
        logo_url = (emp or {}).get("logo_url")
        sales = await self._repo.sales_kpis(empresa_id=empresa_id, period=period)
        daily = await self._repo.daily_sales(empresa_id=empresa_id, days=30)
        monthly = await self._repo.monthly_sales(empresa_id=empresa_id, months=12)
        orders = await self._repo.orders_for_export(
            empresa_id=empresa_id, limit=_DEFAULT_LIMIT
        )
        top_products = await self._repo.top_products(
            empresa_id=empresa_id, limit=_TOP_LIMIT
        )
        kpis = self._build_sales_kpis(sales)
        sections = [
            self._build_sales_section(sales, period),
            ReportSection(
                title="Ventas diarias (últimos 30 días)",
                tables=[
                    ReportTable(
                        title="Tendencia diaria",
                        columns=["Fecha", "Ingresos (S/)", "Pedidos"],
                        rows=[
                            [d["date"], _fmt_money(d["revenue"]), str(d["orders"])]
                            for d in daily
                        ],
                    )
                ],
            ),
            ReportSection(
                title="Ventas mensuales (últimos 12 meses)",
                tables=[
                    ReportTable(
                        title="Tendencia mensual",
                        columns=["Mes", "Ingresos (S/)", "Pedidos"],
                        rows=[
                            [m["month"], _fmt_money(m["revenue"]), str(m["orders"])]
                            for m in monthly
                        ],
                    )
                ],
            ),
            ReportSection(
                title="Top productos",
                tables=[
                    ReportTable(
                        title="Productos más vendidos por unidades",
                        columns=[
                            "Producto",
                            "Unidades",
                            "Ingresos (S/)",
                        ],
                        rows=[
                            [
                                _safe(p["name"], 40),
                                str(p["units_sold"]),
                                _fmt_money(p["revenue"]),
                            ]
                            for p in top_products
                        ],
                    )
                ],
            ),
            ReportSection(
                title="Listado de pedidos",
                tables=[
                    ReportTable(
                        title=f"Detalle de los últimos {len(orders)} pedidos",
                        columns=[
                            "Pedido",
                            "Cliente",
                            "Estado",
                            "Total (S/)",
                            "Tipo de entrega",
                            "Creado",
                        ],
                        rows=[
                            [
                                _safe(o["order_number"], 16),
                                _safe(o["customer_name"], 30),
                                o["status"],
                                _fmt_money(o["total"]),
                                o["delivery_type"],
                                _fmt_date(o["created_at"]),
                            ]
                            for o in orders
                        ],
                    )
                ],
            ),
        ]
        return ExecutiveReportData(
            metadata=ReportMetadata(
                generated_at=self._repo._now(),
                tenant_id=empresa_id,
                tenant_name=tenant_name,
                tenant_logo_url=logo_url,
                period_label=self._build_period_label(period),
                currency="PEN",
            ),
            kpis=kpis,
            sections=sections,
        )

    async def build_inventory_report(
        self, *, empresa_id: UUID
    ) -> ExecutiveReportData:
        period = self._repo._period(self._repo._now())
        emp = await self._repo.get_empresa(empresa_id=empresa_id)
        tenant_name = (emp or {}).get("nombre") or "Empresa"
        logo_url = (emp or {}).get("logo_url")
        inv = await self._repo.inventory_kpis(empresa_id=empresa_id)
        items = await self._repo.inventory_for_export(
            empresa_id=empresa_id, limit=_DEFAULT_LIMIT
        )
        top_products = await self._repo.top_products(
            empresa_id=empresa_id, limit=_TOP_LIMIT
        )
        low_stock = await self._repo.lowest_stock(
            empresa_id=empresa_id, limit=_TOP_LIMIT
        )
        kpis = self._build_inventory_kpis(inv)
        sections = [
            self._build_inventory_section(inv, top_products),
            ReportSection(
                title="Stock crítico",
                tables=[
                    ReportTable(
                        title="Productos con menor stock disponible",
                        columns=[
                            "Producto",
                            "Stock actual",
                            "Stock mínimo",
                            "Reservado",
                            "Estado",
                        ],
                        rows=[
                            [
                                _safe(r["name"], 40),
                                str(r["stock_actual"]),
                                str(r["stock_minimo"]),
                                "0",
                                r["status"],
                            ]
                            for r in low_stock
                        ],
                    )
                ],
            ),
            ReportSection(
                title="Detalle de inventario",
                tables=[
                    ReportTable(
                        title=f"{len(items)} productos en el catálogo",
                        columns=[
                            "Producto",
                            "Categoría",
                            "SKU",
                            "Precio (S/)",
                            "Stock",
                            "Mínimo",
                            "Reservado",
                            "Estado",
                        ],
                        rows=[
                            [
                                _safe(r["name"], 36),
                                _safe(r["category"], 20),
                                _safe(r["sku"], 16),
                                _fmt_money(r["base_price"]),
                                str(r["stock_actual"]),
                                str(r["stock_minimo"]),
                                str(r["stock_reservado"]),
                                r["status"],
                            ]
                            for r in items
                        ],
                    )
                ],
            ),
        ]
        return ExecutiveReportData(
            metadata=ReportMetadata(
                generated_at=self._repo._now(),
                tenant_id=empresa_id,
                tenant_name=tenant_name,
                tenant_logo_url=logo_url,
                period_label=self._build_period_label(period),
                currency="PEN",
            ),
            kpis=kpis,
            sections=sections,
        )

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _build_period_label(period: dict[str, Any]) -> str:
        return (
            f"Hoy: {period['today'].date().isoformat()}, "
            f"Mes: {period['month_start'].date().isoformat()}, "
            f"Año: {period['year_start'].date().isoformat()}"
        )

    @staticmethod
    def _build_executive_kpis(sales, customers, pipeline, inventory) -> list[ReportKPI]:
        return [
            ReportKPI(
                label="Ventas hoy",
                value=_fmt_money(sales["sales_today"]),
                secondary=f"{sales['orders_today']} pedidos",
            ),
            ReportKPI(
                label="Ventas mes",
                value=_fmt_money(sales["sales_month"]),
                secondary=f"{sales['orders_month']} pedidos",
            ),
            ReportKPI(
                label="Ventas año",
                value=_fmt_money(sales["sales_year"]),
                secondary=f"{sales['total_orders']} pedidos histórico",
            ),
            ReportKPI(
                label="Ticket promedio",
                value=_fmt_money(sales["average_ticket"]),
                secondary=f"Mes: {_fmt_money(sales['average_ticket_month'])}",
            ),
            ReportKPI(
                label="Conversión pipeline",
                value=f"{pipeline['conversion_pct']:.1f}%",
                secondary=(
                    f"{pipeline['won_deals']} ganados / "
                    f"{pipeline['lost_deals']} perdidos"
                ),
            ),
            ReportKPI(
                label="Pipeline abierto",
                value=_fmt_money(pipeline["total_value"]),
                secondary=f"Ponderado: {_fmt_money(pipeline['weighted_value'])}",
            ),
            ReportKPI(
                label="Clientes activos",
                value=str(customers["active"]),
                secondary=f"VIP: {customers['vip']}",
            ),
            ReportKPI(
                label="Valor de inventario",
                value=_fmt_money(inventory["inventory_value"]),
                secondary=f"{inventory['total_products']} productos",
            ),
        ]

    @staticmethod
    def _build_pipeline_kpis(pipeline: dict[str, Any]) -> list[ReportKPI]:
        return [
            ReportKPI(
                label="Leads abiertos",
                value=str(pipeline["open_deals"]),
                secondary=_fmt_money(pipeline["total_value"]),
            ),
            ReportKPI(
                label="Leads ganados",
                value=str(pipeline["won_deals"]),
                secondary=_fmt_money(pipeline["won_value"]),
            ),
            ReportKPI(
                label="Leads perdidos",
                value=str(pipeline["lost_deals"]),
                secondary=_fmt_money(pipeline["lost_value"]),
            ),
            ReportKPI(
                label="Conversión",
                value=f"{pipeline['conversion_pct']:.1f}%",
                secondary="Ganados / cerrados",
            ),
        ]

    @staticmethod
    def _build_sales_kpis(sales: dict[str, Any]) -> list[ReportKPI]:
        return [
            ReportKPI(
                label="Ventas hoy",
                value=_fmt_money(sales["sales_today"]),
                secondary=f"{sales['orders_today']} pedidos",
            ),
            ReportKPI(
                label="Ventas mes",
                value=_fmt_money(sales["sales_month"]),
                secondary=f"{sales['orders_month']} pedidos",
            ),
            ReportKPI(
                label="Ticket promedio",
                value=_fmt_money(sales["average_ticket"]),
                secondary="Últimos 30 días",
            ),
            ReportKPI(
                label="Pedidos totales",
                value=str(sales["total_orders"]),
                secondary="Histórico",
            ),
        ]

    @staticmethod
    def _build_crm_kpis(customers: dict[str, Any]) -> list[ReportKPI]:
        return [
            ReportKPI(
                label="Clientes totales",
                value=str(customers["total"]),
                secondary=f"Activos: {customers['active']}",
            ),
            ReportKPI(
                label="Clientes VIP",
                value=str(customers["vip"]),
                secondary="Alto valor",
            ),
            ReportKPI(
                label="Recurrentes",
                value=str(customers["recurrent"]),
                secondary="Múltiples pedidos",
            ),
            ReportKPI(
                label="LTV promedio",
                value=_fmt_money(customers["average_lifetime_value"]),
                secondary=f"Pedidos/cliente: {customers['average_orders_per_customer']}",
            ),
        ]

    @staticmethod
    def _build_inventory_kpis(inv: dict[str, Any]) -> list[ReportKPI]:
        return [
            ReportKPI(
                label="Productos",
                value=str(inv["total_products"]),
                secondary=f"Stock total: {inv['total_units']} u",
            ),
            ReportKPI(
                label="Stock crítico",
                value=str(inv["out_of_stock"]),
                secondary=f"Stock bajo: {inv['low_stock']}",
            ),
            ReportKPI(
                label="Stock normal",
                value=str(inv["normal_stock"]),
                secondary="Disponible",
            ),
            ReportKPI(
                label="Valor inventario",
                value=_fmt_money(inv["inventory_value"]),
                secondary=f"Reservado: {inv['total_reserved_units']} u",
            ),
        ]

    @staticmethod
    def _build_sales_section(
        sales: dict[str, Any], period: dict[str, Any]
    ) -> ReportSection:
        return ReportSection(
            title="Resumen de ventas",
            kpis=[
                ReportKPI(
                    label="Hoy",
                    value=_fmt_money(sales["sales_today"]),
                    secondary=f"{sales['orders_today']} pedidos",
                ),
                ReportKPI(
                    label="Semana",
                    value=_fmt_money(sales["sales_week"]),
                    secondary=f"{sales['orders_week']} pedidos",
                ),
                ReportKPI(
                    label="Mes",
                    value=_fmt_money(sales["sales_month"]),
                    secondary=f"{sales['orders_month']} pedidos",
                ),
                ReportKPI(
                    label="Año",
                    value=_fmt_money(sales["sales_year"]),
                ),
            ],
            tables=[
                ReportTable(
                    title="Ticket promedio",
                    columns=["Periodo", "Ticket promedio (S/)"],
                    rows=[
                        ["Últimos 30 días", _fmt_money(sales["average_ticket"])],
                        ["Mes en curso", _fmt_money(sales["average_ticket_month"])],
                    ],
                )
            ],
        )

    @staticmethod
    def _build_pipeline_section(pipeline: dict[str, Any]) -> ReportSection:
        return ReportSection(
            title="Pipeline comercial",
            kpis=[
                ReportKPI(
                    label="Abiertos",
                    value=str(pipeline["open_deals"]),
                    secondary=_fmt_money(pipeline["total_value"]),
                ),
                ReportKPI(
                    label="Ganados",
                    value=str(pipeline["won_deals"]),
                    secondary=_fmt_money(pipeline["won_value"]),
                ),
                ReportKPI(
                    label="Perdidos",
                    value=str(pipeline["lost_deals"]),
                    secondary=_fmt_money(pipeline["lost_value"]),
                ),
                ReportKPI(
                    label="Conversión",
                    value=f"{pipeline['conversion_pct']:.1f}%",
                    secondary="Ganados / cerrados",
                ),
            ],
        )

    @staticmethod
    def _build_pipeline_overview_section(pipeline: dict[str, Any]) -> ReportSection:
        return ReportSection(
            title="Resumen del pipeline",
            kpis=[
                ReportKPI(
                    label="Valor abierto",
                    value=_fmt_money(pipeline["total_value"]),
                    secondary=f"{pipeline['open_deals']} deals",
                ),
                ReportKPI(
                    label="Valor ponderado",
                    value=_fmt_money(pipeline["weighted_value"]),
                    secondary="Open × probabilidad",
                ),
                ReportKPI(
                    label="Valor ganado",
                    value=_fmt_money(pipeline["won_value"]),
                ),
                ReportKPI(
                    label="Valor perdido",
                    value=_fmt_money(pipeline["lost_value"]),
                ),
            ],
        )

    @staticmethod
    def _build_customers_section(
        customers: dict[str, Any], top_customers: list[dict[str, Any]]
    ) -> ReportSection:
        return ReportSection(
            title="Clientes",
            kpis=[
                ReportKPI(
                    label="Total",
                    value=str(customers["total"]),
                    secondary=f"Activos: {customers['active']}",
                ),
                ReportKPI(
                    label="VIP",
                    value=str(customers["vip"]),
                    secondary="Alto valor",
                ),
                ReportKPI(
                    label="Recurrentes",
                    value=str(customers["recurrent"]),
                ),
                ReportKPI(
                    label="Inactivos",
                    value=str(customers["inactive"]),
                ),
            ],
            tables=[
                ReportTable(
                    title="Top clientes por LTV",
                    columns=["Cliente", "Pedidos", "LTV (S/)", "Categoría"],
                    rows=[
                        [
                            _safe(c["full_name"], 30),
                            str(c["order_count"]),
                            _fmt_money(c["lifetime_value"]),
                            "VIP" if c["is_vip"] else "Recurrente",
                        ]
                        for c in top_customers
                    ],
                )
            ],
        )

    @staticmethod
    def _build_inventory_section(
        inv: dict[str, Any], top_products: list[dict[str, Any]]
    ) -> ReportSection:
        return ReportSection(
            title="Inventario",
            kpis=[
                ReportKPI(
                    label="Total productos",
                    value=str(inv["total_products"]),
                    secondary=f"Stock total: {inv['total_units']} u",
                ),
                ReportKPI(
                    label="Stock crítico",
                    value=str(inv["out_of_stock"]),
                    secondary="Sin unidades",
                ),
                ReportKPI(
                    label="Stock bajo",
                    value=str(inv["low_stock"]),
                    secondary="Por debajo del mínimo",
                ),
                ReportKPI(
                    label="Valor",
                    value=_fmt_money(inv["inventory_value"]),
                ),
            ],
            tables=[
                ReportTable(
                    title="Productos más vendidos",
                    columns=["Producto", "Unidades", "Ingresos (S/)"],
                    rows=[
                        [
                            _safe(p["name"], 40),
                            str(p["units_sold"]),
                            _fmt_money(p["revenue"]),
                        ]
                        for p in top_products
                    ],
                )
            ],
        )

    @staticmethod
    def _build_forecast_section(
        forecast: dict[str, Any], sales: dict[str, Any]
    ) -> ReportSection:
        paragraphs = [
            (
                f"Proyección mensual: {_fmt_money(forecast['monthly'])} "
                f"(confianza: {forecast['confidence']}, muestra: {forecast['sample_size']} meses)."
            ),
            (
                f"Proyección trimestral: {_fmt_money(forecast['quarterly'])} "
                f"basada en el promedio móvil de ventas completadas."
            ),
        ]
        return ReportSection(
            title="Proyecciones IA",
            paragraphs=paragraphs,
            tables=[
                ReportTable(
                    title="Resumen",
                    columns=["Indicador", "Valor"],
                    rows=[
                        ["Ventas año en curso", _fmt_money(sales["sales_year"])],
                        ["Proyección próximo mes", _fmt_money(forecast["monthly"])],
                        ["Proyección próximo trimestre", _fmt_money(forecast["quarterly"])],
                        ["Confianza", forecast["confidence"]],
                        ["Meses analizados", str(forecast["sample_size"])],
                    ],
                )
            ],
        )

    @staticmethod
    def _build_alerts_section(
        inv_alerts: list[str], delayed: list[str]
    ) -> ReportSection:
        return ReportSection(
            title="Alertas críticas",
            paragraphs=(
                ["Inventario crítico:"] + [f"• {a}" for a in inv_alerts]
                + ["Pedidos retrasados:"] + [f"• {a}" for a in delayed]
            ),
            alerts=inv_alerts + delayed,
        )


# ---------------------------------------------------------------------------
# Formatting helpers (private to this module)
# ---------------------------------------------------------------------------
def _fmt_money(value: Decimal | float | int | None) -> str:
    if value is None:
        return "S/ 0.00"
    n = Decimal(str(value))
    sign = "-" if n < 0 else ""
    n_abs = abs(n)
    integer, _, fraction = f"{n_abs:.2f}".partition(".")
    grouped = ""
    while len(integer) > 3:
        grouped = f",{integer[-3:]}{grouped}"
        integer = integer[:-3]
    grouped = f"{integer}{grouped}"
    return f"{sign}S/ {grouped}.{fraction}"


def _fmt_date(value) -> str:
    if value is None:
        return "-"
    try:
        return value.strftime("%Y-%m-%d")
    except Exception:  # noqa: BLE001
        return str(value)


def _safe(value, max_len: int = 30) -> str:
    if value is None:
        return "-"
    s = str(value).strip()
    if not s:
        return "-"
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def _stage_label(stage: str) -> str:
    return {
        "new_lead": "Nuevo Lead",
        "contacted": "Contactado",
        "qualified": "Calificado",
        "proposal": "Propuesta",
        "negotiation": "Negociación",
        "won": "Ganado",
        "lost": "Perdido",
    }.get(stage, stage)


def _customer_category(row: dict[str, Any]) -> str:
    if row.get("is_vip"):
        return "VIP"
    if row.get("is_recurrent"):
        return "Recurrente"
    return "Estándar"


__all__ = ["ReportingService"]
