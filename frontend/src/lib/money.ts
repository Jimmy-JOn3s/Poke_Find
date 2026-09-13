import type { AppLang, Currency } from "../types";


export function formatMoney(amount: number, currency: Currency, locale: AppLang): string {
  const formatted = new Intl.NumberFormat(locale === "th" ? "th-TH" : "en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
  return `${currency === "THB" ? "฿" : "$"}${formatted}`;
}


export function convertAmount(
  amount: number,
  source: Currency,
  target: Currency,
  usdToThb: number,
): number {
  if (usdToThb <= 0) throw new Error("Exchange rate must be positive");
  if (source === target) return amount;
  const converted = source === "USD" ? amount * usdToThb : amount / usdToThb;
  return Math.round((converted + Number.EPSILON) * 100) / 100;
}

