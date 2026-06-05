import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function safeNumber(value: unknown, fallback = 0): number {
  if (value === null || value === undefined) return fallback;
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : fallback;
  }
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (trimmed === "") return fallback;
    const parsed = Number(trimmed);
    return Number.isFinite(parsed) ? parsed : fallback;
  }
  if (typeof value === "boolean") {
    return value ? 1 : 0;
  }
  return fallback;
}

export function safeSum(values: ReadonlyArray<unknown>, fallback = 0): number {
  let total = 0;
  for (const value of values) {
    total += safeNumber(value, 0);
  }
  return Number.isFinite(total) ? total : fallback;
}

export function safeAverage(values: ReadonlyArray<unknown>, fallback = 0): number {
  if (values.length === 0) return fallback;
  const total = safeSum(values, 0);
  const average = total / values.length;
  return Number.isFinite(average) ? average : fallback;
}
