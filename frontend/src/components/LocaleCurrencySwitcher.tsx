import type { AppLang, Currency } from "../types";


interface Props {
  lang: AppLang;
  currency: Currency;
  onLangChange: (lang: AppLang) => void;
  onCurrencyChange: (currency: Currency) => void;
}


export default function LocaleCurrencySwitcher({ lang, currency, onLangChange, onCurrencyChange }: Props) {
  const selectStyle = {
    background: "#0C0E28", border: "1px solid rgba(255,214,0,0.25)",
    borderRadius: 4, color: "#FFD600", fontSize: 13, padding: "10px 12px",
    width: "100%",
  };
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full" aria-label="Language and display currency">
      <select aria-label="Language" value={lang} onChange={event => onLangChange(event.target.value as AppLang)} style={selectStyle}>
        <option value="th">ไทย</option><option value="en">English</option>
      </select>
      <select aria-label="Display currency" value={currency} onChange={event => onCurrencyChange(event.target.value as Currency)} style={selectStyle}>
        <option value="THB">THB ฿</option><option value="USD">USD $</option>
      </select>
    </div>
  );
}
