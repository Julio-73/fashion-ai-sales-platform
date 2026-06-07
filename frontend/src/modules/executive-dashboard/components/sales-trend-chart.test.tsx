import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { SalesTrendChart } from "@/modules/executive-dashboard/components/sales-trend-chart";

afterEach(() => cleanup());

const formatter = new Intl.NumberFormat("es-PE", {
  style: "currency",
  currency: "PEN",
  maximumFractionDigits: 0,
});

// Intl.NumberFormat with PEN uses a non-breaking space (U+00A0) between
// the symbol and the number. We use a regex to match either space.
function currencyMatcher(value: number) {
  const expected = formatter.format(value);
  // Escape regex metachars and replace any whitespace (including U+00A0) with \s+
  const pattern = expected.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/\s+/g, "\\s+");
  return new RegExp(pattern);
}

function renderChart(
  data: Array<{ date: string; revenue: number | string | null | undefined; orders: number }>
) {
  return render(
    <SalesTrendChart
      data={data as unknown as Parameters<typeof SalesTrendChart>[0]["data"]}
      isLoading={false}
    />
  );
}

describe("SalesTrendChart — summary arithmetic", () => {
  it("never renders NaN when revenue comes as strings from the backend (the original bug)", () => {
    // Exact shape of the backend payload: revenue is a string.
    const data = [
      { date: "2026-05-01", revenue: "0", orders: 0 },
      { date: "2026-05-02", revenue: "0", orders: 0 },
      { date: "2026-05-03", revenue: "0", orders: 0 },
    ];
    renderChart(data);

    // The bug was "S/ NaN" appearing in the summary card.
    expect(screen.queryByText(/NaN/)).toBeNull();
    // "S/ 0" appears in 3 places (Promedio, Pico, Total) — confirm at least one.
    expect(screen.getAllByText(currencyMatcher(0)).length).toBeGreaterThanOrEqual(1);
  });

  it("never renders NaN for an empty data array", () => {
    renderChart([]);

    expect(screen.queryByText(/NaN/)).toBeNull();
    expect(screen.getAllByText(currencyMatcher(0)).length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getByText(/Sin datos de ventas en los últimos 30 días/)
    ).toBeInTheDocument();
  });

  it("handles a 30-day window of zero-revenue points without NaN", () => {
    const data = Array.from({ length: 30 }, (_, i) => ({
      date: `2026-04-${String(i + 1).padStart(2, "0")}`,
      revenue: "0",
      orders: 0,
    }));
    renderChart(data);

    expect(screen.queryByText(/NaN/)).toBeNull();
  });

  it("handles a 30-day window of all-undefined revenues without NaN", () => {
    // Defensive: the backend could theoretically omit a field.
    const data = Array.from({ length: 30 }, (_, i) => ({
      date: `2026-04-${String(i + 1).padStart(2, "0")}`,
      revenue: undefined as unknown as number,
      orders: 0,
    }));
    renderChart(data);

    expect(screen.queryByText(/NaN/)).toBeNull();
    expect(screen.getAllByText(currencyMatcher(0)).length).toBeGreaterThanOrEqual(1);
  });

  it("computes the correct total and average when values are numeric", () => {
    const data = [
      { date: "2026-05-01", revenue: 100, orders: 1 },
      { date: "2026-05-02", revenue: 200, orders: 2 },
      { date: "2026-05-03", revenue: 300, orders: 3 },
    ];
    renderChart(data);

    expect(screen.getByText(currencyMatcher(600))).toBeInTheDocument();
    expect(screen.getByText(currencyMatcher(200))).toBeInTheDocument();
    expect(screen.getByText(currencyMatcher(300))).toBeInTheDocument();
  });

  it("computes the correct total and average when values are strings", () => {
    const data = [
      { date: "2026-05-01", revenue: "100", orders: 1 },
      { date: "2026-05-02", revenue: "200", orders: 2 },
      { date: "2026-05-03", revenue: "300", orders: 3 },
    ];
    renderChart(data);

    expect(screen.getByText(currencyMatcher(600))).toBeInTheDocument();
    expect(screen.getByText(currencyMatcher(200))).toBeInTheDocument();
    expect(screen.getByText(currencyMatcher(300))).toBeInTheDocument();
  });

  it("ignores malformed values mixed in with valid ones", () => {
    const data = [
      { date: "2026-05-01", revenue: "100", orders: 1 },
      { date: "2026-05-02", revenue: null as unknown as number, orders: 0 },
      { date: "2026-05-03", revenue: "300", orders: 3 },
    ];
    renderChart(data);

    // Total = 400, average = 133 (400/3)
    expect(screen.getByText(currencyMatcher(400))).toBeInTheDocument();
    expect(screen.queryByText(/NaN/)).toBeNull();
  });

  it("renders the 'Periodo' label with the data length", () => {
    const data = [
      { date: "2026-05-01", revenue: "0", orders: 0 },
      { date: "2026-05-02", revenue: "0", orders: 0 },
    ];
    renderChart(data);

    expect(screen.getByText("2 días")).toBeInTheDocument();
  });

  it("renders '30 días' even when data is empty (header subtitle)", () => {
    renderChart([]);
    expect(screen.getByText(/Ingresos y pedidos en los últimos 30 días/)).toBeInTheDocument();
  });

  it("renders a skeleton when isLoading=true", () => {
    const { container } = render(<SalesTrendChart data={[]} isLoading={true} />);
    const skeletons = container.querySelectorAll(
      '.skeleton-shimmer, .animate-pulse, [role="status"]'
    );
    expect(skeletons.length).toBeGreaterThan(0);
  });
});
