"""PDF generator for the Reporting module.

Single entry point: ``build_executive_pdf(data) -> bytes``. All five
report types (executive, pipeline, crm, sales, inventory) share the
same engine: they are simply different ``ExecutiveReportData``
payloads built by the service layer.
"""
from __future__ import annotations

import io
from datetime import UTC, datetime
from typing import Sequence

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.modules.reporting.generators._common import (
    CURRENCY_SYMBOL,
    fmt_int,
    fmt_money,
    fmt_pct,
    safe_truncate,
)
from app.modules.reporting.schemas import (
    ExecutiveReportData,
    ReportKPI,
    ReportSection,
    ReportTable,
)


# ---------------------------------------------------------------------------
# Color palette — corporate, professional
# ---------------------------------------------------------------------------
_PRIMARY = colors.HexColor("#0F172A")      # slate-900
_ACCENT = colors.HexColor("#2563EB")       # blue-600
_ACCENT_LIGHT = colors.HexColor("#DBEAFE") # blue-100
_BORDER = colors.HexColor("#E2E8F0")       # slate-200
_TEXT = colors.HexColor("#1E293B")         # slate-800
_MUTED = colors.HexColor("#64748B")         # slate-500
_SUCCESS = colors.HexColor("#10B981")      # emerald-500
_WARNING = colors.HexColor("#F59E0B")      # amber-500
_DANGER = colors.HexColor("#EF4444")       # red-500


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------
def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=_PRIMARY,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=_MUTED,
            spaceAfter=12,
        ),
        "section": ParagraphStyle(
            "section",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=_PRIMARY,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "subsection": ParagraphStyle(
            "subsection",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=_TEXT,
            spaceBefore=6,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=_TEXT,
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=_MUTED,
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=_PRIMARY,
        ),
        "kpi_secondary": ParagraphStyle(
            "kpi_secondary",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=_MUTED,
        ),
        "alert": ParagraphStyle(
            "alert",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=_DANGER,
            leftIndent=8,
        ),
        "muted": ParagraphStyle(
            "muted",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=12,
            textColor=_MUTED,
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=_MUTED,
            alignment=TA_CENTER,
        ),
    }
    return styles


# ---------------------------------------------------------------------------
# Page template — header on every page
# ---------------------------------------------------------------------------
def _header_footer(canvas, doc) -> None:  # type: ignore[no-untyped-def]
    canvas.saveState()
    width, _ = A4
    # Top band
    canvas.setFillColor(_PRIMARY)
    canvas.rect(0, A4[1] - 1.2 * cm, width, 1.2 * cm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(
        1.5 * cm, A4[1] - 0.75 * cm, "AI Sales Agent SaaS - Reporte Ejecutivo"
    )
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(
        width - 1.5 * cm,
        A4[1] - 0.75 * cm,
        f"Generado: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}",
    )
    # Footer
    canvas.setFillColor(_MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(
        width / 2.0,
        0.8 * cm,
        f"Página {doc.page}  -  Confidencial  -  {CURRENCY_SYMBOL} en soles peruanos",
    )
    # Bottom rule
    canvas.setStrokeColor(_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(1.5 * cm, 1.4 * cm, width - 1.5 * cm, 1.4 * cm)
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------
def _kpi_table(kpis: Sequence[ReportKPI], styles: dict[str, ParagraphStyle]) -> Table:
    """Render KPIs as a 4-column grid. Cells use the ``kpi_*`` styles."""
    if not kpis:
        return Table([[""]], colWidths=[16 * cm])

    # Pad to a multiple of 4 so we get full rows.
    cells: list[list[object]] = []
    row: list[object] = []
    for kpi in kpis:
        cell = [
            Paragraph(safe_truncate(kpi.label, 40), styles["kpi_label"]),
            Paragraph(_escape(kpi.value), styles["kpi_value"]),
            Paragraph(
                safe_truncate(kpi.secondary or "", 40) if kpi.secondary else "",
                styles["kpi_secondary"],
            ),
        ]
        # Wrap each KPI in a Table for visual card look
        card = Table(
            [[c] for c in cell],
            colWidths=[4.0 * cm],
        )
        card.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), _ACCENT_LIGHT),
                    ("BOX", (0, 0), (-1, -1), 0.5, _BORDER),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        row.append(card)
        if len(row) == 4:
            cells.append(row)
            row = []
    if row:
        while len(row) < 4:
            row.append("")
        cells.append(row)

    grid = Table(cells, colWidths=[4.0 * cm] * 4)
    grid.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return grid


def _data_table(
    table_block: ReportTable, styles: dict[str, ParagraphStyle]
) -> Table:
    headers = [Paragraph(f"<b>{_escape(h)}</b>", styles["body"]) for h in table_block.columns]
    data = [headers]
    for row in table_block.rows:
        data.append([Paragraph(_escape(str(c)), styles["body"]) for c in row])
    if table_block.total_row:
        total_cells = [
            Paragraph(f"<b>{_escape(str(c))}</b>", styles["body"])
            for c in table_block.total_row
        ]
        data.append(total_cells)

    n_cols = max(len(table_block.columns), 1)
    usable_width = 17.0 * cm
    col_widths = [usable_width / n_cols] * n_cols

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), _PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("TEXTCOLOR", (0, 1), (-1, -1), _TEXT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, _PRIMARY),
        ("BOX", (0, 0), (-1, -1), 0.4, _BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 1), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
    ]
    if table_block.total_row:
        style.append(
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F1F5F9"))
        )
        style.append(("LINEABOVE", (0, -1), (-1, -1), 0.6, _PRIMARY))
    t.setStyle(TableStyle(style))
    return t


def _section(
    section: ReportSection, styles: dict[str, ParagraphStyle]
) -> list[object]:
    flow: list[object] = []
    flow.append(Paragraph(_escape(section.title), styles["section"]))
    flow.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER, spaceAfter=4))
    if section.kpis:
        flow.append(Spacer(1, 2 * mm))
        flow.append(_kpi_table(section.kpis, styles))
        flow.append(Spacer(1, 4 * mm))
    for p in section.paragraphs:
        flow.append(Paragraph(_escape(p), styles["body"]))
        flow.append(Spacer(1, 2 * mm))
    for t in section.tables:
        flow.append(
            KeepTogether(
                [
                    Paragraph(_escape(t.title), styles["subsection"]),
                    _data_table(t, styles),
                    Spacer(1, 4 * mm),
                ]
            )
        )
    for a in section.alerts:
        flow.append(Paragraph(f"⚠ {_escape(a)}", styles["alert"]))
        flow.append(Spacer(1, 1 * mm))
    return flow


def _escape(s: str) -> str:
    if not s:
        return ""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def build_executive_pdf(data: ExecutiveReportData) -> bytes:
    """Build the full PDF for the given pre-aggregated report data."""
    styles = _build_styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title=f"Reporte Ejecutivo - {data.metadata.tenant_name}",
        author="AI Sales Agent SaaS",
    )
    flow: list[object] = []
    # Cover block
    flow.append(
        Paragraph(_escape(f"Reporte Ejecutivo - {data.metadata.tenant_name}"), styles["title"])
    )
    period_line = (
        f"Periodo: {data.metadata.period_label}  -  "
        f"Generado: {data.metadata.generated_at.strftime('%Y-%m-%d %H:%M UTC')}  -  "
        f"Moneda: {data.metadata.currency}"
    )
    flow.append(Paragraph(_escape(period_line), styles["subtitle"]))
    flow.append(HRFlowable(width="100%", thickness=1.2, color=_ACCENT, spaceAfter=6))
    # Top KPIs
    if data.kpis:
        flow.append(_kpi_table(data.kpis, styles))
        flow.append(Spacer(1, 6 * mm))
    # Critical alerts
    if data.critical_alerts:
        flow.append(Paragraph("Alertas críticas", styles["section"]))
        for a in data.critical_alerts:
            flow.append(Paragraph(f"⚠ {_escape(a)}", styles["alert"]))
            flow.append(Spacer(1, 1 * mm))
        flow.append(Spacer(1, 4 * mm))
    # Sections
    for section in data.sections:
        flow.extend(_section(section, styles))
        flow.append(Spacer(1, 4 * mm))
    # AI recommendations
    if data.ai_recommendations:
        flow.append(Paragraph("Recomendaciones IA", styles["section"]))
        flow.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER, spaceAfter=4))
        for rec in data.ai_recommendations:
            title = rec.get("title", "")
            desc = rec.get("description", "")
            priority = rec.get("priority", "medium")
            color = (
                _DANGER
                if priority == "high"
                else _WARNING
                if priority == "medium"
                else _SUCCESS
            )
            flow.append(
                Paragraph(
                    f"<font color='{color.hexval()}'>●</font> "
                    f"<b>{_escape(title)}</b> - {_escape(desc)}",
                    styles["body"],
                )
            )
            flow.append(Spacer(1, 1.5 * mm))
        flow.append(Spacer(1, 4 * mm))
    # Footer note
    flow.append(Spacer(1, 1.0 * cm))
    flow.append(
        Paragraph(
            "Documento generado automáticamente por AI Sales Agent SaaS. "
            "La información es confidencial y de uso exclusivo del equipo directivo.",
            styles["muted"],
        )
    )
    doc.build(flow, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Convenience re-exports
# ---------------------------------------------------------------------------
__all__ = ["build_executive_pdf", "fmt_int", "fmt_money", "fmt_pct"]
