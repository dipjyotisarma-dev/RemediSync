import { describe, expect, it } from "vitest";
import {
  formatDaysOfCover,
  formatINR,
  formatPercent,
  formatPerformanceDelta,
} from "@/lib/format";

describe("Clinical formatting utilities", () => {
  it("formats Indian currency using en-IN lakh/thousand grouping", () => {
    expect(formatINR(226534.59, 2)).toBe("₹2,26,534.59");
    expect(formatINR(58000, 0)).toBe("₹58,000");
    expect(formatINR(0, 2)).toBe("₹0.00");
  });

  it("formats fractions and percentages consistently", () => {
    expect(formatPercent(0.018, 1)).toBe("1.8%");
    expect(formatPercent(0, 1)).toBe("0.0%");
  });

  it("formats days of cover and caps extreme/zero-demand horizons", () => {
    expect(formatDaysOfCover(5.64)).toBe("5.6d");
    expect(formatDaysOfCover(1.5)).toBe("1.5d");
    expect(formatDaysOfCover(999)).toBe("99+ d");
  });

  it("formats signed performance delta against target", () => {
    expect(formatPerformanceDelta(1.029)).toBe("+2.9% vs target");
    expect(formatPerformanceDelta(0.945)).toBe("-5.5% vs target");
    expect(formatPerformanceDelta(1.0)).toBe("0.0% vs target");
  });
});
