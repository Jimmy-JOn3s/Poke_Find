import { describe, expect, it } from "vitest";
import { convertAmount, formatMoney } from "./money";


describe("money", () => {
  it("formats Thai baht and US dollars with their locale-aware symbols", () => {
    expect(formatMoney(1234.5, "THB", "th")).toContain("฿1,234.50");
    expect(formatMoney(42, "USD", "en")).toBe("$42.00");
  });

  it("converts in both directions without changing same-currency amounts", () => {
    expect(convertAmount(1000, "THB", "USD", 35)).toBe(28.57);
    expect(convertAmount(10.25, "USD", "THB", 35)).toBe(358.75);
    expect(convertAmount(10.25, "USD", "USD", 35)).toBe(10.25);
  });
});

