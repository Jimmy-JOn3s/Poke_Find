import type { AppLang, User } from '../types';
import { i18n } from '../i18n';
import { MOCK_LISTINGS } from '../mockData';

interface Props {
  lang: AppLang;
  currentUser: User | null;
  onBack: () => void;
}

const MONTHLY_DATA = [
  { month: 'มี.ค.', monthEn: 'Mar', revenue: 32000, transactions: 8 },
  { month: 'เม.ย.', monthEn: 'Apr', revenue: 48000, transactions: 12 },
  { month: 'พ.ค.', monthEn: 'May', revenue: 41000, transactions: 10 },
  { month: 'มิ.ย.', monthEn: 'Jun', revenue: 67000, transactions: 18 },
  { month: 'ก.ค.', monthEn: 'Jul', revenue: 89000, transactions: 24 },
  { month: 'ส.ค.', monthEn: 'Aug', revenue: 72000, transactions: 19 },
];

const TOP_CARDS = [
  { name: 'Charizard ex (Full Art)', sold: 14, revenue: 119000, icon: '🔥' },
  { name: 'ピカチュウex (Special Art)', sold: 8, revenue: 96000, icon: '⚡' },
  { name: 'Gardevoir ex (Alt Art)', sold: 12, revenue: 62400, icon: '✨' },
  { name: 'Rayquaza VMAX', sold: 3, revenue: 43500, icon: '🐉' },
  { name: 'Mew ex (Full Art)', sold: 9, revenue: 34200, icon: '🔮' },
];

const RECENT_SALES = [
  { card: 'Charizard ex (Full Art)', buyer: 'นภัส รักการ์ด', price: 8000, dateTh: '25 ส.ค.', dateEn: '25 Aug', icon: '🔥' },
  { card: 'ピカチュウex', buyer: 'Sakura TH', price: 11500, dateTh: '24 ส.ค.', dateEn: '24 Aug', icon: '⚡' },
  { card: 'Gardevoir ex', buyer: 'มานะ เพชรดี', price: 5000, dateTh: '22 ส.ค.', dateEn: '22 Aug', icon: '✨' },
  { card: 'Rayquaza VMAX', buyer: 'Anonymous', price: 13800, dateTh: '20 ส.ค.', dateEn: '20 Aug', icon: '🐉' },
];

export default function AnalyticsPage({ lang, currentUser, onBack }: Props) {
  const t = i18n[lang];

  if (!currentUser || currentUser.role !== 'business') {
    return (
      <div className="flex flex-col items-center justify-center h-full px-6 text-center pb-20 pixel-bg">
        <div className="text-5xl mb-4">🔒</div>
        <h2 className="font-display text-lg font-bold text-foreground mb-2">{t.businessOnly}</h2>
        <p className="text-muted-foreground text-sm mb-6">{lang === 'th' ? 'ฟีเจอร์นี้ใช้ได้เฉพาะบัญชีธุรกิจที่ยืนยันแล้ว' : 'This feature is only available for verified business accounts'}</p>
        <button onClick={onBack} className="px-6 py-3 text-sm font-bold font-display"
          style={{ border: '1px solid rgba(255,255,255,0.12)', borderRadius: 4, color: '#7880AA' }}>
          {t.back}
        </button>
      </div>
    );
  }

  const maxRevenue = Math.max(...MONTHLY_DATA.map(d => d.revenue));
  const totalRevenue = MONTHLY_DATA.reduce((s, d) => s + d.revenue, 0);
  const totalTx = MONTHLY_DATA.reduce((s, d) => s + d.transactions, 0);
  const myListings = MOCK_LISTINGS.filter(l => l.sellerId === 'me');

  return (
    <div className="flex flex-col min-h-full bg-background pixel-bg">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 pt-12 pb-4 shrink-0"
        style={{ background: 'rgba(6,7,26,0.97)', backdropFilter: 'blur(20px)', borderBottom: '1px solid rgba(255,214,0,0.1)', position: 'sticky', top: 0, zIndex: 10 }}>
        <button onClick={onBack}
          className="w-8 h-8 flex items-center justify-center font-display text-muted-foreground"
          style={{ border: '1px solid rgba(255,255,255,0.1)', borderRadius: 4, background: 'rgba(255,255,255,0.05)' }}>←</button>
        <div>
          <h1 className="font-display text-lg font-bold" style={{ color: '#FFD600', textShadow: '0 0 10px rgba(255,214,0,0.4)' }}>{t.analyticsTitle}</h1>
          <p className="text-xs text-muted-foreground font-mono">{t.lastSixMonths}</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 bottom-safe flex flex-col gap-4">
        {/* KPIs */}
        <div className="grid grid-cols-2 gap-2.5">
          {[
            { label: t.revenue, value: `฿${(totalRevenue / 1000).toFixed(0)}K`, sub: `+23%`, color: '#FFD600', icon: '💰' },
            { label: t.transactions, value: totalTx.toString(), sub: `${t.avgTx} ${(totalTx / 6).toFixed(1)} ${t.perMonth}`, color: '#FF2EBD', icon: '🤝' },
            { label: t.activeListings, value: myListings.length.toString(), sub: `${myListings.filter(l => l.status === 'active').length} ${t.available}`, color: '#00E676', icon: '📦' },
            { label: t.avgRating, value: `★ ${currentUser.rating}`, sub: `${currentUser.reviewCount} ${t.reviews}`, color: '#FFB300', icon: '⭐' },
          ].map(kpi => (
            <div key={kpi.label} className="p-4"
              style={{ background: '#0C0E28', border: `1px solid ${kpi.color}22`, borderRadius: 6, boxShadow: `2px 2px 0 ${kpi.color}20` }}>
              <div className="text-xl mb-2">{kpi.icon}</div>
              <p className="text-2xl font-bold font-mono" style={{ color: kpi.color }}>{kpi.value}</p>
              <p className="font-display text-xs text-muted-foreground mt-0.5">{kpi.label}</p>
              <p className="text-[10px] mt-1" style={{ color: kpi.color, opacity: 0.7 }}>{kpi.sub}</p>
            </div>
          ))}
        </div>

        {/* Revenue chart */}
        <div className="p-4" style={{ background: '#0C0E28', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 6 }}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display font-semibold text-sm text-foreground">{t.revenue}</h2>
            <span className="text-xs text-muted-foreground font-mono">฿{totalRevenue.toLocaleString()}</span>
          </div>
          <div className="flex items-end gap-1.5 h-24">
            {MONTHLY_DATA.map((d, i) => {
              const pct = (d.revenue / maxRevenue) * 100;
              const isCurrent = i === MONTHLY_DATA.length - 1;
              return (
                <div key={d.month} className="flex-1 flex flex-col items-center gap-1">
                  <div className="w-full transition-all"
                    style={{
                      height: `${pct}%`, minHeight: 4,
                      background: isCurrent ? 'linear-gradient(to top, #FFD600, #FFE566)' : 'rgba(255,214,0,0.35)',
                      borderRadius: '2px 2px 0 0',
                      boxShadow: isCurrent ? '0 0 8px rgba(255,214,0,0.4)' : 'none',
                    }} />
                  <span className="text-[9px] text-muted-foreground font-mono">{lang === 'th' ? d.month : d.monthEn}</span>
                </div>
              );
            })}
          </div>
          {/* Tx count row */}
          <div className="flex justify-between mt-3 pt-3" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
            {MONTHLY_DATA.map(d => (
              <div key={d.month} className="flex-1 text-center">
                <p className="font-mono text-[10px]" style={{ color: '#FF2EBD' }}>{d.transactions}</p>
              </div>
            ))}
          </div>
          <p className="text-[10px] text-muted-foreground mt-1 text-center font-display">{t.txCount}</p>
        </div>

        {/* Top cards */}
        <div style={{ background: '#0C0E28', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 6, overflow: 'hidden' }}>
          <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
            <h2 className="font-display font-semibold text-sm text-foreground">{t.topCards}</h2>
            <span className="text-xs text-muted-foreground font-mono">{t.lastSixMonths}</span>
          </div>
          {TOP_CARDS.map((card, i) => {
            const maxSold = TOP_CARDS[0].sold;
            return (
              <div key={card.name} className="flex items-center gap-3 px-4 py-3" style={{ borderBottom: i < TOP_CARDS.length - 1 ? '1px solid rgba(255,255,255,0.04)' : undefined }}>
                <span className="font-pixel text-[9px] text-muted-foreground w-4">{i + 1}</span>
                <span className="text-lg">{card.icon}</span>
                <div className="flex-1 min-w-0">
                  <p className="font-display text-xs font-semibold text-foreground truncate">{card.name}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="flex-1 h-1 overflow-hidden" style={{ background: 'rgba(255,255,255,0.07)', borderRadius: 1 }}>
                      <div className="h-full" style={{ width: `${(card.sold / maxSold) * 100}%`, background: '#FFD600', boxShadow: '0 0 4px rgba(255,214,0,0.5)' }} />
                    </div>
                    <span className="text-[10px] text-muted-foreground font-mono shrink-0">{card.sold} {lang === 'th' ? 'ชิ้น' : 'pcs'}</span>
                  </div>
                </div>
                <span className="text-xs font-mono font-bold shrink-0" style={{ color: '#FFD600' }}>฿{(card.revenue / 1000).toFixed(0)}K</span>
              </div>
            );
          })}
        </div>

        {/* Recent sales */}
        <div style={{ background: '#0C0E28', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 6, overflow: 'hidden' }}>
          <div className="px-4 py-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
            <h2 className="font-display font-semibold text-sm text-foreground">{t.recentSales}</h2>
          </div>
          {RECENT_SALES.map((sale, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-3" style={{ borderBottom: i < RECENT_SALES.length - 1 ? '1px solid rgba(255,255,255,0.04)' : undefined }}>
              <div className="w-9 h-9 flex items-center justify-center text-lg shrink-0"
                style={{ background: 'rgba(255,214,0,0.08)', borderRadius: 4, border: '1px solid rgba(255,214,0,0.15)' }}>
                {sale.icon}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-display text-xs font-semibold text-foreground truncate">{sale.card}</p>
                <p className="text-[10px] text-muted-foreground">{sale.buyer} · {lang === 'th' ? sale.dateTh : sale.dateEn}</p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-sm font-bold font-mono" style={{ color: '#00E676' }}>+฿{sale.price.toLocaleString()}</p>
                <p className="font-display text-[10px]" style={{ color: '#00E676', opacity: 0.7 }}>✓ {t.txSuccess}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
