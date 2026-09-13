import { useState } from 'react';
import type { Listing, AppLang, Currency, User } from '../types';
import { i18n } from '../i18n';
import { MOCK_USERS } from '../mockData';
import Price from '../components/Price';

interface Props {
  listing: Listing;
  lang: AppLang;
  currentUser: User | null;
  onBack: () => void;
  onChat: (listing: Listing) => void;
  onViewProfile: (userId: string) => void;
  onEditListing?: (listing: Listing) => void;
  onDeleteListing?: (listingId: string) => void;
  displayCurrency: Currency;
}

export default function ListingDetailPage({ listing, lang, currentUser, onBack, onChat, onViewProfile, onEditListing, onDeleteListing, displayCurrency }: Props) {
  const t = i18n[lang];
  const [liked, setLiked] = useState(false);
  const [showDelete, setShowDelete] = useState(false);
  const isOwner = currentUser?.id === listing.sellerId;
  const seller = MOCK_USERS.find(u => u.id === listing.sellerId) || {
    id: listing.sellerId, name: listing.sellerName, avatar: listing.sellerAvatar,
    role: listing.sellerRole, verified: listing.sellerVerified, rating: listing.sellerRating,
    reviewCount: 0, totalSold: 0,
  };

  const conditionColor = (c: string) =>
    ({ M: '#00E676', NM: '#69F0AE', LP: '#FFD600', MP: '#FF9800', HP: '#FF3D57' }[c] || '#7880AA');

  const rarityLabel = listing.rarity === 'secret' ? t.raritySecret : listing.rarity === 'ultra' ? t.rarityUltra : t.rarityRare;
  const conditionFull = { M: t.M, NM: t.NM, LP: t.LP, MP: t.MP, HP: t.HP }[listing.condition];
  const langLabel = { th: `🇹🇭 ${t.th}`, en: `🇺🇸 ${t.en}`, ja: '🇯🇵 日本語' }[listing.language];

  return (
    <div className="flex flex-col min-h-full bg-background">
      {/* Card art hero */}
      <div className="relative h-72 flex items-center justify-center overflow-hidden scanlines"
        style={{ background: `linear-gradient(160deg, ${listing.gradientFrom}33 0%, ${listing.gradientTo}55 100%)` }}>
        <div className="absolute inset-0" style={{ background: `linear-gradient(135deg, ${listing.gradientFrom}25 0%, ${listing.gradientTo}45 100%)` }} />
        <div className="relative z-10 text-8xl" style={{ filter: 'drop-shadow(0 4px 16px rgba(0,0,0,0.7))' }}>{listing.typeIcon}</div>

        <button onClick={onBack}
          className="absolute top-12 left-4 z-20 w-9 h-9 flex items-center justify-center font-display"
          style={{ background: 'rgba(6,7,26,0.8)', backdropFilter: 'blur(12px)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 4 }}>
          ←
        </button>

        <button onClick={() => setLiked(!liked)}
          className="absolute top-12 right-4 z-20 w-9 h-9 flex items-center justify-center transition-all"
          style={{ background: liked ? 'rgba(255,46,189,0.3)' : 'rgba(6,7,26,0.8)', backdropFilter: 'blur(12px)', border: `1px solid ${liked ? 'rgba(255,46,189,0.5)' : 'rgba(255,255,255,0.12)'}`, borderRadius: 4, color: liked ? '#FF2EBD' : '#F0F0FF' }}>
          ♥
        </button>

        <div className="absolute bottom-4 left-4 font-pixel text-[9px] px-2 py-1"
          style={{ background: 'rgba(6,7,26,0.9)', color: '#FFD600', border: '1px solid rgba(255,214,0,0.3)', borderRadius: 2 }}>
          {rarityLabel}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto" style={{ paddingBottom: isOwner ? '1rem' : '5rem' }}>
        <div className="px-4 pt-4">
          {/* Title row */}
          <div className="flex items-start justify-between gap-3 mb-1">
            <h1 className="font-display text-lg font-bold text-foreground leading-tight flex-1">{listing.productName}</h1>
            {isOwner && (
              <div className="flex gap-1.5 shrink-0">
                <button onClick={() => onEditListing?.(listing)}
                  className="px-2.5 py-1 text-xs font-bold font-display"
                  style={{ border: '1px solid rgba(255,255,255,0.1)', borderRadius: 3, color: '#7880AA' }}>
                  {t.editListing}
                </button>
                <button onClick={() => setShowDelete(true)}
                  className="px-2.5 py-1 text-xs font-bold font-display"
                  style={{ border: '1px solid rgba(255,61,87,0.3)', borderRadius: 3, color: '#FF3D57' }}>
                  {t.deleteListing}
                </button>
              </div>
            )}
          </div>
          <p className="text-muted-foreground text-sm mb-3 font-mono">{listing.set} · #{listing.cardNumber}</p>

          {/* Price block */}
          <div className="flex items-center justify-between p-4 mb-4"
            style={{ background: 'rgba(255,214,0,0.05)', border: '1px solid rgba(255,214,0,0.2)', borderRadius: 6, boxShadow: '3px 3px 0 rgba(255,214,0,0.1)' }}>
            <div>
              <p className="font-display text-xs text-muted-foreground mb-0.5">{t.listedPrice}</p>
              <Price amount={listing.listedPrice} currency={listing.currency} displayCurrency={displayCurrency} lang={lang}
                className="text-2xl font-bold font-mono" />
            </div>
            <div className="text-right">
              <p className="font-display text-xs text-muted-foreground mb-0.5">{t.quantity}</p>
              <p className="text-xl font-bold font-mono text-foreground">{listing.quantity}</p>
            </div>
          </div>

          {/* Details grid */}
          <div className="grid grid-cols-2 gap-2 mb-4">
            {[
              { label: t.condition, value: conditionFull, color: conditionColor(listing.condition) },
              { label: t.language, value: langLabel },
              { label: t.sellerType, value: listing.sellerRole === 'business' ? `🏪 ${t.business}` : `👤 ${t.personal}` },
              { label: t.views,     value: `${listing.views.toLocaleString()}` },
            ].map(({ label, value, color }) => (
              <div key={label} className="p-3" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 4 }}>
                <p className="font-display text-xs text-muted-foreground mb-1">{label}</p>
                <p className="font-display text-sm font-semibold" style={{ color: color || '#E8E8FF' }}>{value}</p>
              </div>
            ))}
          </div>

          {/* Seller card */}
          {seller && (
            <button onClick={() => onViewProfile(listing.sellerId)}
              className="w-full flex items-center gap-3 p-4 text-left mb-4 transition-all card-hover"
              style={{ background: '#0C0E28', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 6 }}>
              <div className="w-11 h-11 flex items-center justify-center text-base font-bold shrink-0"
                style={{ background: 'linear-gradient(135deg, #3B1874, #FF2EBD)', color: '#fff', borderRadius: 6 }}>
                {seller.avatar}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="font-display font-bold text-sm text-foreground truncate">{seller.name}</span>
                  {seller.role === 'business' && <span className="badge-business">{t.businessBadge}</span>}
                  {seller.verified && <span className="badge-verified">✓</span>}
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
                  <span>★ {seller.rating}</span>
                  <span>·</span>
                  <span>{seller.reviewCount} {t.reviews}</span>
                  <span>·</span>
                  <span>{t.sold} {seller.totalSold}</span>
                </div>
              </div>
              <span className="font-pixel text-[10px]" style={{ color: '#7880AA' }}>→</span>
            </button>
          )}

          {/* Meta */}
          <div className="flex gap-3 text-xs text-muted-foreground font-mono mb-2">
            <span>♥ {liked ? listing.likes + 1 : listing.likes}</span>
            <span>·</span>
            <span>👁 {listing.views}</span>
            <span>·</span>
            <span>{t.postedOn} {listing.createdAt}</span>
          </div>
        </div>
      </div>

      {/* CTA */}
      {!isOwner && (
        <div className="fixed bottom-0 left-0 right-0 px-4 py-3 max-w-lg mx-auto"
          style={{ background: 'rgba(6,7,26,0.97)', backdropFilter: 'blur(20px)', borderTop: '1px solid rgba(255,214,0,0.15)' }}>
          <button onClick={() => onChat(listing)}
            className="w-full py-4 text-sm font-bold font-display flex items-center justify-center gap-2 btn-primary"
            style={{ borderRadius: 4 }}>
            💬 {t.contactSeller} / {t.makeOffer}
          </button>
        </div>
      )}

      {/* Delete confirm */}
      {showDelete && (
        <div className="fixed inset-0 z-50 flex items-end justify-center animate-fade-in"
          style={{ background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(12px)' }}>
          <div className="w-full max-w-lg p-5 border-t"
            style={{ background: '#0C0E28', borderColor: 'rgba(255,61,87,0.2)', borderRadius: '8px 8px 0 0' }}>
            <h3 className="font-display text-lg font-bold text-foreground mb-2">{t.deleteListing}</h3>
            <p className="text-muted-foreground text-sm mb-2">{t.deleteConfirm}</p>
            <p className="text-xs text-muted-foreground mb-5">{t.deleteWarning}</p>
            <div className="flex gap-3">
              <button onClick={() => setShowDelete(false)}
                className="flex-1 py-3 text-sm font-bold font-display"
                style={{ border: '1px solid rgba(255,255,255,0.1)', borderRadius: 4, color: '#7880AA' }}>
                {t.cancel}
              </button>
              <button onClick={() => { onDeleteListing?.(listing.id); setShowDelete(false); onBack(); }}
                className="flex-1 py-3 text-sm font-bold font-display"
                style={{ background: 'rgba(255,61,87,0.12)', color: '#FF3D57', border: '1px solid rgba(255,61,87,0.3)', borderRadius: 4, boxShadow: '2px 2px 0 rgba(180,0,30,0.3)' }}>
                {t.deleteListing}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
