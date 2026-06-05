import { describe, expect, it } from "vitest";

import { safeAverage, safeNumber, safeSum } from "@/lib/utils";

describe("safeNumber", () => {
  it("returns 0 for null, undefined, empty string, and whitespace", () => {
    expect(safeNumber(null)).toBe(0);
    expect(safeNumber(undefined)).toBe(0);
    expect(safeNumber("")).toBe(0);
    expect(safeNumber("   ")).toBe(0);
  });

  it("returns the value for finite numbers", () => {
    expect(safeNumber(0)).toBe(0);
    expect(safeNumber(42)).toBe(42);
    expect(safeNumber(-12.5)).toBe(-12.5);
  });

  it("returns the fallback for NaN and Infinity", () => {
    expect(safeNumber(NaN)).toBe(0);
    expect(safeNumber(Infinity)).toBe(0);
    expect(safeNumber(-Infinity)).toBe(0);
    expect(safeNumber(NaN, 99)).toBe(99);
    expect(safeNumber(Infinity, 99)).toBe(99);
  });

  it("parses valid numeric strings", () => {
    expect(safeNumber("0")).toBe(0);
    expect(safeNumber("42")).toBe(42);
    expect(safeNumber("  12.5  ")).toBe(12.5);
    expect(safeNumber("-3.14")).toBe(-3.14);
  });

  it("returns the fallback for non-numeric strings", () => {
    expect(safeNumber("abc")).toBe(0);
    expect(safeNumber("NaN")).toBe(0);
    expect(safeNumber("Infinity")).toBe(0);
    expect(safeNumber("abc", 7)).toBe(7);
  });

  it("returns the fallback for unsupported types", () => {
    expect(safeNumber({})).toBe(0);
    expect(safeNumber([])).toBe(0);
    expect(safeNumber([1])).toBe(0);
  });

  it("coerces booleans to 0/1", () => {
    expect(safeNumber(true)).toBe(1);
    expect(safeNumber(false)).toBe(0);
  });
});

describe("safeSum", () => {
  it("returns 0 for an empty array", () => {
    expect(safeSum([])).toBe(0);
  });

  it("sums numeric values", () => {
    expect(safeSum([1, 2, 3])).toBe(6);
  });

  it("sums string values that look like numbers (the S/ NaN regression)", () => {
    // The bug: `total += "0"` produced "00" (string concat).
    // The fix: safeSum normalises strings to numbers before adding.
    expect(safeSum(["0", "0", "0"])).toBe(0);
    expect(safeSum(["100.50", "200.25", "50"])).toBe(350.75);
  });

  it("ignores invalid values (null, undefined, NaN, garbage strings)", () => {
    expect(safeSum([null, undefined, "abc", 5])).toBe(5);
  });

  it("returns the fallback if the result is non-finite", () => {
    // The helper defends against pathological cases (overflow).
    // MAX_VALUE + MAX_VALUE overflows to Infinity in JS, so safeSum
    // catches the non-finite result and returns the fallback.
    const huge = Number.MAX_VALUE;
    expect(safeSum([huge, huge])).toBe(0);
    expect(safeSum([huge, huge], 99)).toBe(99);
  });
});

describe("safeAverage", () => {
  it("returns the fallback for an empty array (avoids 0/0 = NaN)", () => {
    expect(safeAverage([])).toBe(0);
    expect(safeAverage([], 42)).toBe(42);
  });

  it("computes a simple arithmetic mean", () => {
    expect(safeAverage([10, 20, 30])).toBe(20);
  });

  it("averages over string values without NaN (the S/ NaN regression)", () => {
    // This is the exact bug the user reported:
    // backend returns revenue as strings; "0" + "0" + "0" was "000", "/30" was NaN.
    expect(safeAverage(["0", "0", "0"])).toBe(0);
    expect(safeAverage(["100", "200", "300"])).toBe(200);
  });

  it("treats null/undefined/garbage as 0 in the sum but counts them in the denominator", () => {
    // This matches the executive-dashboard use case: a fixed window of N days
    // where some days have no data. The period average should be sum/N,
    // not sum/(N-with-data).
    // [null, "10", undefined, "20", "abc"] -> sum=30, count=5 -> 6
    expect(safeAverage([null, "10", undefined, "20", "abc"])).toBe(6);
  });

  it("returns the fallback (not 0) for an empty array", () => {
    expect(safeAverage([])).toBe(0);
    expect(safeAverage([], 99)).toBe(99);
  });

  it("never returns NaN even with mixed garbage", () => {
    const result = safeAverage([NaN, "abc", null]);
    expect(Number.isNaN(result)).toBe(false);
    expect(result).toBe(0);
  });
});
