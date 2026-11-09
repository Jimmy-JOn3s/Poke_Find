import { useEffect, useState } from "react";
import type { AppLang, User } from "../types";
import { i18n } from "../i18n";
import { api, type BusinessAnalytics } from "../lib/api";
import { formatMoney } from "../lib/money";

interface Props {
  lang: AppLang;
  currentUser: User | null;
  onBack: () => void;
}

function monthLabel(isoMonth: string, lang: AppLang): string {
  const date = new Date(`${isoMonth}T00:00:00`);
  return new Intl.DateTimeFormat(lang === "th" ? "th-TH" : "en-US", { month: "short" }).format(date);
}

export default function AnalyticsPage({ lang, currentUser, onBack }: Props) {
  const t = i18n[lang];
  const [data, setData] = useState<BusinessAnalytics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!currentUser || currentUser.role !== "business") return;
    setLoading(true);
    setError("");
    api.analyticsMe()
      .then(setData)
      .catch(caught => setError(caught instanceof Error ? caught.message : "Request failed"))
      .finally(() => setLoading(false));
  }, [currentUser?.id, currentUser?.role]);

  if (!currentUser || currentUser.role !== "business") {
    return (
      <div className="flex flex-col items-center justify-center h-full px-6 text-center pb-20 pixel-bg">
        <div className="text-5xl mb-4">🔒</div>
        <h2 className="font-display text-lg font-bold text-foreground mb-2">{t.businessOnly}</h2>
        <p className="text-muted-foreground text-sm mb-6">{lang === "th" ? "ฟีเจอร์นี้ใช้ได้เฉพาะบัญชีธุรกิจ" : "This feature is only available for business accounts."}</p>
        <button onClick={onBack} className="px-6 py-3 text-sm font-bold font-display chip-btn-outline">{t.back}</button>
      </div>
    );
  }

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center h-full px-6 text-center pb-20 pixel-bg">
        <p className="text-sm text-muted-foreground">{t.loading}</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex flex-col items-center justify-center h-full px-6 text-center pb-20 pixel-bg">
        <p className="text-sm text-danger mb-4">{error || t.networkError}</p>
        <button onClick={onBack} className="px-6 py-3 text-sm font-bold font-display chip-btn-outline">{t.back}</button>
      </div>
    );
  }

  const chartCurrency = data.chart_currency;
  const totalRevenue = Number(data.revenue_by_currency[chartCurrency] || 0);
  const maxRevenue = Math.max(...data.monthly.map(row => Number(row.revenue)), 1);
  const noSalesYet = data.transactions === 0;

  return (
    <div className="page-shell bg-background pixel-bg">
      <div className="page-container flex items-center gap-3 px-4 md:px-6 lg:px-8 page-header pb-4 shrink-0 page-header-bar">
        <button onClick={onBack}
          className="w-8 h-8 flex items-center justify-center font-display text-muted-foreground chip-btn-outline">←</button>
        <div>
          <h1 className="font-display text-lg font-bold page-title">{t.analyticsTitle}</h1>
          <p className="text-xs text-muted-foreground font-mono">{t.lastSixMonths}</p>
        </div>
      </div>

      <div className="page-scroll scroll-end-buffer px-4 md:px-6 lg:px-8 py-4 space-y-4 page-container max-w-5xl w-full">
        {noSalesYet && (
          <p className="text-sm text-muted-foreground text-center px-2">{t.comingSoonHint}</p>
        )}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 md:gap-3">
          {[
            {
              label: t.revenue,
              value: formatMoney(totalRevenue, chartCurrency, lang),
              sub: Object.entries(data.revenue_by_currency)
                .filter(([code]) => code !== chartCurrency)
                .map(([code, amount]) => formatMoney(Number(amount), code as typeof chartCurrency, lang))
                .join(" · ") || chartCurrency,
              icon: "💰",
            },
            { label: t.transactions, value: String(data.transactions), sub: `${data.deals_active} ${lang === "th" ? "ดีลค้าง" : "active deals"}`, icon: "🤝" },
            { label: t.activeListings, value: String(data.listings.total), sub: `${data.listings.active} ${t.available}`, icon: "📦" },
            { label: t.avgRating, value: `★ ${data.rating}`, sub: `${data.review_count} ${t.reviews}`, icon: "⭐" },
          ].map(kpi => (
            <div key={kpi.label} className="p-4 panel-card">
              <div className="text-xl mb-2">{kpi.icon}</div>
              <p className="text-2xl font-bold font-mono text-primary">{kpi.value}</p>
              <p className="font-display text-xs text-muted-foreground mt-0.5">{kpi.label}</p>
              <p className="text-[10px] mt-1 text-muted-foreground">{kpi.sub}</p>
            </div>
          ))}
        </div>

        <div className="p-4 panel-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display font-semibold text-sm text-foreground">{t.revenue}</h2>
            <span className="text-xs text-muted-foreground font-mono">{formatMoney(totalRevenue, chartCurrency, lang)}</span>
          </div>
          <div className="flex items-end gap-1.5 h-24">
            {data.monthly.map((row, index) => {
              const amount = Number(row.revenue);
              const pct = maxRevenue > 0 ? (amount / maxRevenue) * 100 : 0;
              const isCurrent = index === data.monthly.length - 1;
              return (
                <div key={row.month} className="flex-1 flex flex-col items-center gap-1">
                  <div className="w-full transition-all"
                    style={{
                      height: `${pct}%`,
                      minHeight: amount > 0 ? 4 : 0,
                      background: isCurrent
                        ? "linear-gradient(to top, var(--color-primary), color-mix(in srgb, var(--color-primary) 70%, white))"
                        : "color-mix(in srgb, var(--color-primary) 35%, transparent)",
                      borderRadius: "2px 2px 0 0",
                    }} />
                  <span className="text-[9px] text-muted-foreground font-mono">{monthLabel(row.month, lang)}</span>
                </div>
              );
            })}
          </div>
          <p className="text-[10px] text-muted-foreground mt-2 text-center font-display">{chartCurrency} · {t.txCount}</p>
        </div>

        {data.top_cards.length > 0 && (
          <div className="panel-card">
            <div className="px-4 py-3 panel-divider">
              <h2 className="font-display font-semibold text-sm text-foreground">{t.topCards}</h2>
            </div>
            {data.top_cards.map((card, index) => (
                <div key={`${card.name}-${index}`} className={`flex items-center gap-3 px-4 py-3 min-w-0 ${index < data.top_cards.length - 1 ? "panel-divider" : ""}`}>
                  <span className="font-pixel text-[9px] text-muted-foreground w-4">{index + 1}</span>
                  <div className="flex-1 min-w-0">
                    <p className="font-display text-xs font-semibold text-foreground truncate">{card.name}</p>
                    <p className="text-[10px] text-muted-foreground">{card.sold} {lang === "th" ? "ชิ้น" : "sold"}</p>
                  </div>
                  <span className="text-xs font-mono font-bold text-primary shrink-0">
                    {formatMoney(Number(card.revenue), card.currency as typeof chartCurrency, lang)}
                  </span>
                </div>
            ))}
          </div>
        )}

        {data.recent_sales.length > 0 && (
          <div className="panel-card">
            <div className="px-4 py-3 panel-divider">
              <h2 className="font-display font-semibold text-sm text-foreground">{t.recentSales}</h2>
            </div>
            {data.recent_sales.map((sale, index) => (
              <div key={`${sale.completed_at}-${index}`} className={`flex items-center gap-3 px-4 py-3 min-w-0 ${index < data.recent_sales.length - 1 ? "panel-divider" : ""}`}>
                <div className="flex-1 min-w-0">
                  <p className="font-display text-xs font-semibold text-foreground truncate">{sale.card_name}</p>
                  <p className="text-[10px] text-muted-foreground">
                    {sale.buyer_name} · {new Intl.DateTimeFormat(lang === "th" ? "th-TH" : "en-US", { month: "short", day: "numeric" }).format(new Date(sale.completed_at))}
                  </p>
                </div>
                <p className="text-sm font-bold font-mono text-success">
                  +{formatMoney(Number(sale.price), sale.currency, lang)}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
