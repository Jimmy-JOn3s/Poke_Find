import { useState, useMemo } from 'react';
import type { Listing, AppLang, CardCondition, CardLanguage, Currency } from '../types';
import { i18n } from '../i18n';
import { SETS } from '../mockData';
import Price from '../components/Price';

interface Props {
  lang: AppLang;
  onSelectListing: (l: Listing) => void;
  onCreateListing: () => void;
  isAuthenticated: boolean;
  listings: Listing[];
  loading?: boolean;
  error?: string;
  displayCurrency: Currency;
  onRetry?: () => void;
}

const CONDITIONS: CardCondition[] = ['M', 'NM', 'LP', 'MP', 'HP'];
const LANGUAGES: CardLanguage[] = ['th', 'en'];

export default function DiscoverPage({ lang, onSelectListing, onCreateListing, isAuthenticated, listings, loading, error, displayCurrency, onRetry }: Props) {
  const t = i18n[lang];
  const [search, setSearch] = useState('');
  const [filterCondition, setFilterCondition] = useState('');
  const [filterLang, setFilterLang] = useState('');
  const [filterSet, setFilterSet] = useState('');
  const [sortBy, setSortBy] = useState('newest');
  const [showFilters, setShowFilters] = useState(false);

  const sortLabels: Record<string, string> = {
    newest: t.sortNewest, popular: t.sortPopular, price_asc: t.sortPriceLow, price_desc: t.sortPriceHigh,
  };

  const filtered = useMemo(() => {
    let list = [...listings];
    if (search) list = list.filter(l => l.productName.toLowerCase().includes(search.toLowerCase()) || l.set.toLowerCase().includes(search.toLowerCase()));
    if (filterCondition) list = list.filter(l => l.condition === filterCondition);
    if (filterLang) list = list.filter(l => l.language === filterLang);
    if (filterSet) list = list.filter(l => l.set === filterSet);
    if (sortBy === 'price_asc') list.sort((a, b) => a.listedPrice - b.listedPrice);
    else if (sortBy === 'price_desc') list.sort((a, b) => b.listedPrice - a.listedPrice);
    else if (sortBy === 'popular') list.sort((a, b) => b.likes - a.likes);
    else list.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
    return list;
  }, [listings, search, filterCondition, filterLang, filterSet, sortBy]);

  const activeFilters = [filterCondition, filterLang, filterSet].filter(Boolean).length;

  return (
    <div className="flex flex-col h-full pixel-bg">
      {/* Header */}
      <div className="page-container px-4 md:px-6 lg:px-8 page-header pb-3 shrink-0"
        style={{ background: 'rgba(6,7,26,0.97)', backdropFilter: 'blur(20px)', position: 'sticky', top: 0, zIndex: 10, borderBottom: '1px solid rgba(255,214,0,0.1)' }}>
        <div className="flex items-center justify-between mb-3 gap-4">
          <div>
            <h1 className="font-display text-xl font-bold" style={{ color: '#FFD600', textShadow: '0 0 12px rgba(255,214,0,0.5)' }}>
              {t.discoverTitle}
            </h1>
          </div>
          {isAuthenticated && (
            <button onClick={onCreateListing} className="btn-primary flex items-center gap-1.5 px-3 py-2 rounded text-xs font-bold">
              + {t.createListing}
            </button>
          )}
        </div>

        {/* Search */}
        <div className="relative mb-2">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 opacity-40" width="14" height="14" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="3" width="12" height="12" stroke="#F0F0FF" strokeWidth="2" />
            <path d="M17 17L21 21" stroke="#F0F0FF" strokeWidth="2" strokeLinecap="square" />
          </svg>
          <input type="text" value={search} onChange={e => setSearch(e.target.value)}
            aria-label={t.searchPlaceholder}
            placeholder={t.searchPlaceholder}
            className="w-full pl-8 pr-4 py-2.5 text-sm text-foreground"
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 4, fontFamily: "'Sarabun', sans-serif" }} />
        </div>

        {/* Filter row */}
        <div className="flex gap-2 overflow-x-auto md:overflow-visible md:flex-wrap pb-1 scroll-hide">
          <button onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-1 px-3 py-1.5 text-xs font-semibold shrink-0 transition-all"
            style={{
              background: showFilters || activeFilters > 0 ? 'rgba(255,214,0,0.15)' : 'rgba(255,255,255,0.05)',
              border: `1px solid ${showFilters || activeFilters > 0 ? 'rgba(255,214,0,0.5)' : 'rgba(255,255,255,0.08)'}`,
              borderRadius: 4,
              color: showFilters || activeFilters > 0 ? '#FFD600' : '#7880AA',
              fontFamily: "'Chakra Petch', sans-serif",
            }}>
            ⚙ {t.filter}
            {activeFilters > 0 && (
              <span className="ml-1 px-1.5 rounded text-[9px] font-pixel" style={{ background: '#FFD600', color: '#06071A' }}>{activeFilters}</span>
            )}
          </button>
          {(['newest', 'popular', 'price_asc', 'price_desc'] as const).map(s => (
            <button key={s} onClick={() => setSortBy(s)}
              className="px-3 py-1.5 text-xs font-semibold shrink-0 transition-all"
              style={{
                background: sortBy === s ? 'rgba(255,214,0,0.15)' : 'rgba(255,255,255,0.05)',
                border: `1px solid ${sortBy === s ? 'rgba(255,214,0,0.5)' : 'rgba(255,255,255,0.08)'}`,
                borderRadius: 4,
                color: sortBy === s ? '#FFD600' : '#7880AA',
                fontFamily: "'Chakra Petch', sans-serif",
              }}>
              {sortLabels[s]}
            </button>
          ))}
        </div>

        {showFilters && (
          <div className="mt-2 p-3 grid grid-cols-1 sm:grid-cols-3 gap-2 animate-slide-up"
            style={{ background: 'rgba(12,14,40,0.98)', border: '1px solid rgba(255,214,0,0.15)', borderRadius: 4 }}>
            {[
              { value: filterCondition, onChange: setFilterCondition, placeholder: t.allConditions, options: CONDITIONS.map(c => ({ v: c, l: t[c] })) },
              { value: filterLang, onChange: setFilterLang, placeholder: t.allLanguages, options: LANGUAGES.map(l => ({ v: l, l: t[l] })) },
              { value: filterSet, onChange: setFilterSet, placeholder: t.allSets, options: SETS.map(s => ({ v: s, l: s })) },
            ].map((sel, i) => (
              <select key={i} value={sel.value} onChange={e => sel.onChange(e.target.value)} aria-label={sel.placeholder}
                className="text-xs text-foreground px-2 py-1.5"
                style={{ background: '#0C0E28', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 3, fontFamily: "'Sarabun', sans-serif" }}>
                <option value="">{sel.placeholder}</option>
                {sel.options.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
              </select>
            ))}
          </div>
        )}
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-y-auto px-3 md:px-6 lg:px-8 bottom-safe">
        {loading && <p className="text-center text-sm text-muted-foreground py-8">{t.loading}</p>}
        {error && (
          <div className="text-center py-8">
            <p className="text-sm mb-3" style={{ color: '#FF3D57' }}>{t.networkError}: {error}</p>
            <button className="btn-primary px-4 py-2 text-xs" onClick={onRetry}>{t.tryAgain}</button>
          </div>
        )}
        <div className="page-container grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-2.5 md:gap-3 lg:gap-4 pt-3 pb-6">
          {filtered.map(listing => (
            <ListingCard key={listing.id} listing={listing} t={t} lang={lang} displayCurrency={displayCurrency} onClick={() => onSelectListing(listing)} />
          ))}
        </div>
        {filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="text-5xl mb-4">🔍</div>
            <p className="font-display text-sm" style={{ color: '#FFD600' }}>{t.noResults}</p>
            <p className="text-xs text-muted-foreground mt-1">{t.noResultsSub}</p>
          </div>
        )}
      </div>
    </div>
  );
}

function ListingCard({ listing, t, lang, displayCurrency, onClick }: { listing: Listing; t: (typeof i18n)[AppLang]; lang: AppLang; displayCurrency: Currency; onClick: () => void }) {
  const rarityBorder: Record<string, string> = {
    common: 'rgba(200,200,200,0.2)', uncommon: 'rgba(34,197,94,0.35)',
    rare: 'rgba(96,165,250,0.35)', ultra: 'rgba(168,85,247,0.45)', secret: 'rgba(255,214,0,0.5)',
  };

  return (
    <button onClick={onClick} className="text-left overflow-hidden card-hover"
      style={{ background: '#0C0E28', borderRadius: 6, border: `1px solid ${rarityBorder[listing.rarity] || 'rgba(255,255,255,0.06)'}` }}>
      {/* Card art */}
      <div className="relative aspect-[2.5/3.5] flex items-center justify-center overflow-hidden scanlines"
        style={{ background: `linear-gradient(135deg, ${listing.gradientFrom}25, ${listing.gradientTo}40)` }}>
        <div className="absolute inset-0" style={{ background: `linear-gradient(160deg, ${listing.gradientFrom}30 0%, ${listing.gradientTo}50 100%)` }} />
        <div className="relative z-10 text-5xl" style={{ filter: 'drop-shadow(0 2px 8px rgba(0,0,0,0.6))' }}>{listing.typeIcon}</div>
        {/* Condition */}
        <div className="absolute top-1.5 left-1.5 px-1.5 py-0.5 font-pixel text-[8px]"
          style={{ background: 'rgba(6,7,26,0.9)', color: conditionColor(listing.condition), borderRadius: 2, border: `1px solid ${conditionColor(listing.condition)}40` }}>
          {listing.condition}
        </div>
        {/* Language */}
        <div className="absolute top-1.5 right-1.5 px-1.5 py-0.5 text-[9px] font-semibold"
          style={{ background: 'rgba(6,7,26,0.9)', color: '#7880AA', borderRadius: 2, fontFamily: "'Chakra Petch', sans-serif" }}>
          {listing.language.toUpperCase()}
        </div>
        {listing.sellerRole === 'business' && (
          <div className="absolute bottom-1.5 left-1.5 badge-business">{t.businessBadge}</div>
        )}
        {listing.sellerVerified && (
          <div className="absolute bottom-1.5 right-1.5 badge-verified">✓</div>
        )}
      </div>

      {/* Info */}
      <div className="p-2">
        <p className="text-xs font-semibold text-foreground leading-tight line-clamp-2 mb-0.5"
          style={{ fontFamily: "'Chakra Petch', sans-serif" }}>{listing.productName}</p>
        <p className="text-[10px] text-muted-foreground line-clamp-1 mb-1.5">{listing.set}</p>
        <div className="flex items-center justify-between">
          <Price amount={listing.listedPrice} currency={listing.currency} displayCurrency={displayCurrency} lang={lang}
            className="text-sm font-bold font-mono" />
          <span className="text-[10px] text-muted-foreground">♥ {listing.likes}</span>
        </div>
      </div>
    </button>
  );
}

function conditionColor(c: CardCondition) {
  return { M: '#00E676', NM: '#69F0AE', LP: '#FFD600', MP: '#FF9800', HP: '#FF3D57' }[c] || '#7880AA';
}
