import { useState } from 'react';
import type { AppLang, Currency, User, Listing, Review } from '../types';
import { i18n } from '../i18n';
import Price from '../components/Price';

interface Props {
  lang: AppLang;
  currentUser: User | null;
  listings: Listing[];
  displayCurrency: Currency;
  viewUserId?: string;
  isAuthenticated: boolean;
  onSignIn: () => void;
  onSelectListing: (l: Listing) => void;
  onViewAnalytics: () => void;
}

export default function ProfilePage({ lang, currentUser, listings, displayCurrency, viewUserId, isAuthenticated, onSignIn, onSelectListing, onViewAnalytics }: Props) {
  const t = i18n[lang];
  const [tab, setTab] = useState<'listings' | 'reviews'>('listings');

  const sellerListing = viewUserId ? listings.find(listing => listing.sellerId === viewUserId) : undefined;
  const profileUser = sellerListing ? {
    id: sellerListing.sellerId,
    name: sellerListing.sellerName,
    email: '',
    avatar: sellerListing.sellerAvatar,
    role: sellerListing.sellerRole,
    verified: sellerListing.sellerVerified,
    rating: sellerListing.sellerRating,
    reviewCount: 0,
    totalSold: 0,
    joinedDate: '',
    location: '',
    bio: '',
  } satisfies User : currentUser;
  const isOwnProfile = !viewUserId || viewUserId === currentUser?.id;

  if (!isAuthenticated && isOwnProfile) {
    return (
      <div className="flex flex-col items-center justify-center h-full px-6 text-center pb-20 pixel-bg">
        <div className="text-5xl mb-4">👤</div>
        <h2 className="font-display text-lg font-bold text-foreground mb-2">{t.profile}</h2>
        <p className="text-muted-foreground text-sm mb-6">{lang === 'th' ? 'เข้าสู่ระบบเพื่อดูโปรไฟล์ของคุณ' : 'Sign in to view your profile'}</p>
        <button onClick={onSignIn} className="px-8 py-3 text-sm font-bold btn-primary" style={{ borderRadius: 4 }}>
          {t.signIn}
        </button>
      </div>
    );
  }

  if (!profileUser) return null;

  const userListings = listings.filter(l => l.sellerId === profileUser.id);
  const reviews: Review[] = [];

  return (
    <div className="flex flex-col min-h-full bg-background">
      {/* Profile hero */}
      <div className="relative pt-12 pixel-bg"
        style={{ background: 'linear-gradient(160deg, #1A0A3D 0%, #06071A 70%)' }}>
        <div className="absolute inset-0" style={{ background: 'radial-gradient(ellipse at 50% 0%, rgba(59,24,116,0.5) 0%, transparent 70%)' }} />
        <div className="relative px-4 pb-5 flex flex-col items-center text-center">
          {/* Avatar */}
          <div className="w-18 h-18 w-[72px] h-[72px] flex items-center justify-center text-2xl font-bold mb-3 relative"
            style={{ background: 'linear-gradient(135deg, #3B1874, #FF2EBD)', color: '#fff', borderRadius: 8, boxShadow: '3px 3px 0 rgba(255,46,189,0.4)' }}>
            {profileUser.avatar}
            {profileUser.verified && (
              <div className="absolute -bottom-1 -right-1 w-6 h-6 flex items-center justify-center text-xs border-2"
                style={{ background: '#00E676', borderColor: '#06071A', color: '#06071A', fontWeight: 900, borderRadius: 3 }}>✓</div>
            )}
          </div>

          {/* Name + badges */}
          <div className="flex items-center gap-2 mb-1">
            <h1 className="font-display text-lg font-bold text-foreground">{profileUser.name}</h1>
            {profileUser.role === 'business' && <span className="badge-business">{t.businessBadge}</span>}
          </div>

          {/* Verification */}
          <div className="flex items-center gap-3 text-xs mb-2">
            {profileUser.verified ? (
              <span className="font-display flex items-center gap-1" style={{ color: '#00E676' }}>
                ✓ {t.verified} {profileUser.verifiedType === 'passport' ? `(${t.passport})` : `(${t.idCard})`}
              </span>
            ) : (
              <span className="font-display opacity-50 text-muted-foreground">○ {t.notVerified}</span>
            )}
            <span className="text-muted-foreground">•</span>
            <span className="text-muted-foreground">📍 {profileUser.location}</span>
          </div>

          {profileUser.bio && (
            <p className="text-sm text-muted-foreground max-w-xs leading-relaxed mb-4">{profileUser.bio}</p>
          )}

          {/* Stats bar */}
          <div className="flex w-full max-w-sm overflow-hidden"
            style={{ border: '1px solid rgba(255,214,0,0.15)', borderRadius: 4, background: 'rgba(255,255,255,0.03)', boxShadow: '2px 2px 0 rgba(255,214,0,0.08)' }}>
            {[
              { label: t.totalSold, value: profileUser.totalSold.toLocaleString() },
              { label: t.rating,    value: `★ ${profileUser.rating}` },
              { label: t.reviews,   value: profileUser.reviewCount.toString() },
            ].map((stat, i) => (
              <div key={stat.label} className="flex-1 py-3 text-center" style={{ borderRight: i < 2 ? '1px solid rgba(255,214,0,0.1)' : undefined }}>
                <p className="font-mono font-bold text-base" style={{ color: '#FFD600' }}>{stat.value}</p>
                <p className="text-[10px] text-muted-foreground font-display">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Business analytics button */}
      {isOwnProfile && profileUser.role === 'business' && (
        <div className="px-4 pt-3">
          <button onClick={onViewAnalytics}
            className="w-full flex items-center justify-between p-4 transition-all"
            style={{ background: 'rgba(255,214,0,0.05)', border: '1px solid rgba(255,214,0,0.2)', borderRadius: 6, boxShadow: '2px 2px 0 rgba(255,214,0,0.1)' }}>
            <div className="flex items-center gap-3">
              <div className="text-xl">📊</div>
              <div className="text-left">
                <p className="font-display font-semibold text-sm text-foreground">{t.analyticsTitle}</p>
                <p className="text-xs text-muted-foreground">{t.businessOnly}</p>
              </div>
            </div>
            <span className="font-pixel text-[10px]" style={{ color: '#FFD600' }}>→</span>
          </button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex px-4 pt-3 gap-2">
        {(['listings', 'reviews'] as const).map(tabId => (
          <button key={tabId} onClick={() => setTab(tabId)}
            className="flex-1 py-2.5 text-sm font-bold font-display transition-all"
            style={{
              background: tab === tabId ? 'rgba(255,214,0,0.1)' : 'rgba(255,255,255,0.03)',
              border: `1px solid ${tab === tabId ? 'rgba(255,214,0,0.4)' : 'rgba(255,255,255,0.07)'}`,
              borderRadius: 4,
              color: tab === tabId ? '#FFD600' : '#7880AA',
              boxShadow: tab === tabId ? '2px 2px 0 rgba(255,214,0,0.15)' : 'none',
            }}>
            {tabId === 'listings' ? `${t.activeListings} (${userListings.length})` : `${t.reviews} (${reviews.length})`}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 pt-3 pb-4 bottom-safe">
        {tab === 'listings' && (
          <div className="grid grid-cols-2 gap-2.5">
            {userListings.length === 0 ? (
              <div className="col-span-2 py-12 text-center">
                <p className="font-display text-sm text-muted-foreground">{t.noListings}</p>
              </div>
            ) : (
              userListings.map(listing => (
                <button key={listing.id} onClick={() => onSelectListing(listing)}
                  className="text-left overflow-hidden transition-all card-hover"
                  style={{
                    background: '#0C0E28', borderRadius: 6,
                    border: `1px solid ${listing.status === 'completed' ? 'rgba(0,230,118,0.3)' : 'rgba(255,255,255,0.06)'}`,
                  }}>
                  <div className="relative aspect-square flex items-center justify-center scanlines"
                    style={{ background: `linear-gradient(135deg, ${listing.gradientFrom}33, ${listing.gradientTo}44)` }}>
                    <span className="text-4xl">{listing.typeIcon}</span>
                    {listing.status === 'completed' && (
                      <div className="absolute inset-0 flex items-center justify-center"
                        style={{ background: 'rgba(0,230,118,0.12)' }}>
                        <span className="font-pixel text-[8px] px-2 py-1" style={{ background: 'rgba(0,230,118,0.9)', color: '#06071A', borderRadius: 2 }}>✓ {t.sold}</span>
                      </div>
                    )}
                  </div>
                  <div className="p-2">
                    <p className="font-display text-xs font-semibold text-foreground line-clamp-1 mb-0.5">{listing.productName}</p>
                    <Price amount={listing.listedPrice} currency={listing.currency ?? 'THB'} displayCurrency={displayCurrency} lang={lang} className="text-sm font-bold font-mono" />
                  </div>
                </button>
              ))
            )}
          </div>
        )}

        {tab === 'reviews' && (
          <div className="flex flex-col gap-3">
            {reviews.length === 0 ? (
              <div className="py-12 text-center">
                <p className="font-display text-sm text-muted-foreground">{t.noReviews}</p>
              </div>
            ) : (
              reviews.map(review => (
                <div key={review.id} className="p-4"
                  style={{ background: '#0C0E28', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 6 }}>
                  <div className="flex items-start gap-3 mb-2">
                    <div className="w-9 h-9 flex items-center justify-center text-sm font-bold shrink-0"
                      style={{ background: 'linear-gradient(135deg, #3B1874, #FF2EBD)', color: '#fff', borderRadius: 4 }}>
                      {review.reviewerAvatar}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-display font-semibold text-sm text-foreground truncate">{review.reviewerName}</span>
                        {review.reviewerRole === 'business' && <span className="badge-business">{t.businessBadge}</span>}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <div className="flex">
                          {Array.from({ length: 5 }).map((_, i) => (
                            <span key={i} className="font-pixel text-[10px]" style={{ color: i < review.rating ? '#FFD600' : '#2A2D50' }}>★</span>
                          ))}
                        </div>
                        <span className="text-[10px] text-muted-foreground font-mono">{review.date}</span>
                      </div>
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground leading-relaxed">{review.comment}</p>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
