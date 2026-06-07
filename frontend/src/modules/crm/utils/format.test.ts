import { describe, expect, it } from "vitest";

import {
  formatCurrency,
  formatDate,
  formatDateTime,
  formatNumber
} from "@/modules/crm/utils/format";

describe("formatCurrency", () => {
  it("returns '—' for null/undefined", () => {
    expect(formatCurrency(null)).toBe("—");
    expect(formatCurrency(undefined)).toBe("—");
  });

  it("returns '—' for non-finite values", () => {
    expect(formatCurrency("abc")).toBe("—");
    expect(formatCurrency(NaN)).toBe("—");
  });

  it("formats numbers as currency", () => {
    const result = formatCurrency(1234.56);
    expect(result).toMatch(/1[\s.,]?234/);
  });

  it("accepts numeric strings", () => {
    const result = formatCurrency("1234.5");
    expect(result).toMatch(/1[\s.,]?234/);
  });
});

describe("formatNumber", () => {
  it("returns '—' for null/undefined", () => {
    expect(formatNumber(null)).toBe("—");
    expect(formatNumber(undefined)).toBe("—");
  });

  it("formats numbers with locale separator", () => {
    const result = formatNumber(1234567);
    expect(result).toMatch(/1[\s.,]?234[\s.,]?567/);
  });
});

describe("formatDate", () => {
  it("returns '—' for empty values", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDate(undefined)).toBe("—");
    expect(formatDate("")).toBe("—");
  });

  it("returns '—' for invalid dates", () => {
    expect(formatDate("not-a-date")).toBe("—");
  });

  it("formats a valid ISO date", () => {
    const result = formatDate("2026-05-01T00:00:00Z");
    expect(result).toMatch(/2026/);
  });
});

describe("formatDateTime", () => {
  it("returns '—' for empty values", () => {
    expect(formatDateTime(null)).toBe("—");
  });

  it("formats a valid ISO datetime with time", () => {
    const result = formatDateTime("2026-05-01T15:30:00Z");
    expect(result).toMatch(/2026/);
    expect(result.length).toBeGreaterThan(5);
  });
});
