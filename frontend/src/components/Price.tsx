import type { AppLang, Currency } from "../types";
import { convertAmount, formatMoney } from "../lib/money";


interface Props {
  amount: number;
  currency?: Currency;
  displayCurrency: Currency;
  lang: AppLang;
  usdToThb?: number;
  className?: string;
}


export default function Price({ amount, currency = "THB", displayCurrency, lang, usdToThb = 35, className }: Props) {
  const displayed = convertAmount(amount, currency, displayCurrency, usdToThb);
  return <span className={className}>{formatMoney(displayed, displayCurrency, lang)}</span>;
}

