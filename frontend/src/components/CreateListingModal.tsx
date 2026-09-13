import { useState } from 'react';
import type { AppLang, CardCondition, CardLanguage, Currency, Listing, UserRole } from '../types';
import { i18n } from '../i18n';
import { SETS } from '../mockData';

interface Props {
  lang: AppLang;
  onClose: () => void;
  onSubmit: (listing: Partial<Listing>) => void;
  editListing?: Listing;
  sellerRole: UserRole;
}

const CONDITIONS: { value: CardCondition }[] = [
  { value: 'M' }, { value: 'NM' }, { value: 'LP' }, { value: 'MP' }, { value: 'HP' },
];

const LANGUAGES: { value: CardLanguage; flag: string }[] = [
  { value: 'th', flag: '🇹🇭' },
  { value: 'en', flag: '🇺🇸' },
];

const TYPE_ICONS = ['🔥', '💧', '🌿', '⚡', '🔮', '🌙', '🐉', '✨', '⚪', '⚔️'];

const GRAD_PRESETS = [
  ['#FF4500', '#FF8C00'], ['#FFD700', '#FFA500'], ['#9B59B6', '#E91E8C'],
  ['#06B6D4', '#0EA5E9'], ['#E91E8C', '#9C27B0'], ['#1A1A2E', '#4A0080'],
  ['#22C55E', '#16A34A'], ['#FF6B35', '#FF4500'],
];

export default function CreateListingModal({ lang, onClose, onSubmit, editListing, sellerRole }: Props) {
  const t = i18n[lang];
  const [step, setStep] = useState(1);
  const [productName, setProductName] = useState(editListing?.productName || '');
  const [set, setSet] = useState(editListing?.set || '');
  const [cardNumber, setCardNumber] = useState(editListing?.cardNumber || '');
  const [condition, setCondition] = useState<CardCondition>(editListing?.condition || 'NM');
  const [cardLang, setCardLang] = useState<CardLanguage>(editListing?.language || 'th');
  const [price, setPrice] = useState(editListing?.listedPrice?.toString() || '');
  const [currency, setCurrency] = useState<Currency>(editListing?.currency || 'THB');
  const [quantity, setQuantity] = useState(editListing?.quantity?.toString() || '1');
  const [typeIcon, setTypeIcon] = useState(editListing?.typeIcon || '✨');
  const [gradIdx, setGradIdx] = useState(0);

  const [gradientFrom, gradientTo] = editListing ? [editListing.gradientFrom, editListing.gradientTo] : GRAD_PRESETS[gradIdx];

  const totalSteps = 3;
  const canNext1 = productName.trim() && set && cardNumber.trim();
  const canNext2 = price && parseInt(price) > 0;

  const inputStyle = {
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.09)',
    borderRadius: 4,
    color: '#F0F0FF',
    fontFamily: "'Sarabun', sans-serif",
    fontSize: 14,
    width: '100%',
    padding: '12px 16px',
  };

  const conditionColor = (c: CardCondition) =>
    ({ M: '#00E676', NM: '#69F0AE', LP: '#FFD600', MP: '#FF9800', HP: '#FF3D57' }[c]);

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center animate-fade-in modal-above-nav"
      style={{ background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(14px)' }}>
      <div className="w-full max-w-lg flex flex-col"
        style={{ background: '#090B22', border: '1px solid rgba(255,214,0,0.15)', borderRadius: '8px 8px 0 0', maxHeight: '90vh', boxShadow: '0 -3px 0 rgba(255,214,0,0.12)' }}>
        {/* Header */}
        <div className="flex items-center justify-between px-5 pt-5 pb-4 shrink-0" style={{ borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
          <div>
            <p className="font-pixel text-[8px] mb-1" style={{ color: '#FF2EBD' }}>
              {t.step} {step} {t.of} {totalSteps}
            </p>
            <h2 className="font-display text-lg font-bold text-foreground">
              {editListing ? t.editListing : t.createListing}
            </h2>
          </div>
          <button onClick={onClose}
            className="w-8 h-8 flex items-center justify-center font-display text-muted-foreground"
            style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.09)', borderRadius: 4 }}>✕</button>
        </div>

        {/* Progress */}
        <div className="flex gap-1 px-5 py-2.5 shrink-0">
          {Array.from({ length: totalSteps }).map((_, i) => (
            <div key={i} className="flex-1 h-1 transition-all"
              style={{ background: step > i ? '#FFD600' : 'rgba(255,255,255,0.08)', borderRadius: 1 }} />
          ))}
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto px-5 pb-4">
          {/* Step 1: Card info */}
          {step === 1 && (
            <div className="flex flex-col gap-4 pt-2 animate-slide-up">
              <div>
                <label className="font-pixel text-[8px] uppercase tracking-wider mb-2 block" style={{ color: '#FFD600' }}>{t.productName}</label>
                <input type="text" value={productName} onChange={e => setProductName(e.target.value)}
                  aria-label={t.productName}
                  placeholder={lang === 'th' ? 'เช่น Charizard ex (Full Art)' : 'e.g. Charizard ex (Full Art)'}
                  style={inputStyle} />
              </div>

              <div>
                <label className="font-pixel text-[8px] uppercase tracking-wider mb-2 block" style={{ color: '#FFD600' }}>{t.set}</label>
                <select value={set} onChange={e => setSet(e.target.value)} aria-label={t.set} style={{ ...inputStyle }}>
                  <option value="">{t.selectSet}</option>
                  {SETS.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>

              <div>
                <label className="font-pixel text-[8px] uppercase tracking-wider mb-2 block" style={{ color: '#FFD600' }}>{t.cardNumber}</label>
                <input type="text" value={cardNumber} onChange={e => setCardNumber(e.target.value)}
                  aria-label={t.cardNumber}
                  placeholder="125/197"
                  style={{ ...inputStyle, fontFamily: "'DM Mono', monospace" }} />
              </div>

              <div>
                <label className="font-pixel text-[8px] uppercase tracking-wider mb-2 block" style={{ color: '#FFD600' }}>{t.language}</label>
                <div className="flex gap-2">
                  {LANGUAGES.map(l => (
                    <button key={l.value} onClick={() => setCardLang(l.value)}
                      className="flex-1 py-3 text-sm font-bold font-display transition-all"
                      style={{
                        background: cardLang === l.value ? 'rgba(255,214,0,0.1)' : 'transparent',
                        border: `1px solid ${cardLang === l.value ? 'rgba(255,214,0,0.4)' : 'rgba(255,255,255,0.09)'}`,
                        borderRadius: 4,
                        color: cardLang === l.value ? '#FFD600' : '#7880AA',
                        boxShadow: cardLang === l.value ? '2px 2px 0 rgba(255,214,0,0.15)' : 'none',
                      }}>
                      {l.flag} {t[l.value]}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="font-pixel text-[8px] uppercase tracking-wider mb-2 block" style={{ color: '#FFD600' }}>{t.typeIconLabel}</label>
                <div className="flex flex-wrap gap-2">
                  {TYPE_ICONS.map(icon => (
                    <button key={icon} onClick={() => setTypeIcon(icon)}
                      className="w-10 h-10 text-xl flex items-center justify-center transition-all"
                      style={{
                        background: typeIcon === icon ? 'rgba(255,214,0,0.12)' : 'rgba(255,255,255,0.04)',
                        border: `1px solid ${typeIcon === icon ? 'rgba(255,214,0,0.4)' : 'rgba(255,255,255,0.07)'}`,
                        borderRadius: 4,
                        boxShadow: typeIcon === icon ? '2px 2px 0 rgba(255,214,0,0.2)' : 'none',
                      }}>
                      {icon}
                    </button>
                  ))}
                </div>
              </div>

              {!editListing && (
                <div>
                  <label className="font-pixel text-[8px] uppercase tracking-wider mb-2 block" style={{ color: '#FFD600' }}>
                    {lang === 'th' ? 'สีการ์ด' : 'Card Color'}
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {GRAD_PRESETS.map(([from, to], i) => (
                      <button key={i} onClick={() => setGradIdx(i)}
                        className="w-9 h-9 transition-all"
                        style={{
                          background: `linear-gradient(135deg, ${from}, ${to})`,
                          borderRadius: 4,
                          border: gradIdx === i ? '2px solid #FFD600' : '2px solid transparent',
                          boxShadow: gradIdx === i ? '0 0 6px rgba(255,214,0,0.5)' : 'none',
                        }} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Condition + Price */}
          {step === 2 && (
            <div className="flex flex-col gap-4 pt-2 animate-slide-up">
              <div>
                <label className="font-pixel text-[8px] uppercase tracking-wider mb-2 block" style={{ color: '#FFD600' }}>{t.condition}</label>
                <div className="flex flex-col gap-2">
                  {CONDITIONS.map(c => (
                    <button key={c.value} onClick={() => setCondition(c.value)}
                      className="flex items-center gap-3 px-4 py-3 text-left transition-all"
                      style={{
                        background: condition === c.value ? 'rgba(255,214,0,0.05)' : 'rgba(255,255,255,0.03)',
                        border: `1px solid ${condition === c.value ? 'rgba(255,214,0,0.35)' : 'rgba(255,255,255,0.07)'}`,
                        borderRadius: 4,
                        boxShadow: condition === c.value ? '2px 2px 0 rgba(255,214,0,0.15)' : 'none',
                      }}>
                      <span className="font-pixel text-[9px] w-8" style={{ color: conditionColor(c.value) }}>{c.value}</span>
                      <span className="font-display text-sm" style={{ color: condition === c.value ? '#FFD600' : '#E8E8FF' }}>{t[c.value]}</span>
                      {condition === c.value && <span className="ml-auto font-pixel text-[8px]" style={{ color: '#FFD600' }}>✓</span>}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="font-pixel text-[8px] uppercase tracking-wider mb-2 block" style={{ color: '#FFD600' }}>{t.listedPrice}</label>
                <div className="flex gap-2 mb-2">
                  {(['THB', 'USD'] as Currency[]).map(code => (
                    <button key={code} onClick={() => setCurrency(code)} className="flex-1 py-2 text-xs font-bold"
                      style={{ border: `1px solid ${currency === code ? '#FFD600' : 'rgba(255,255,255,0.09)'}`, color: currency === code ? '#FFD600' : '#7880AA', borderRadius: 4 }}>
                      {code} {code === 'THB' ? '฿' : '$'}
                    </button>
                  ))}
                </div>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 font-bold font-mono" style={{ color: '#FFD600' }}>{currency === 'THB' ? '฿' : '$'}</span>
                  <input type="number" value={price} onChange={e => setPrice(e.target.value)}
                    aria-label={`${t.listedPrice} (${currency})`}
                    placeholder="0"
                    style={{ ...inputStyle, paddingLeft: 32, textAlign: 'right', fontFamily: "'DM Mono', monospace" }} />
                </div>
              </div>

              <div>
                <label className="font-pixel text-[8px] uppercase tracking-wider mb-2 block" style={{ color: '#FFD600' }}>{t.quantity}</label>
                <div className="flex items-center gap-3">
                  <button onClick={() => setQuantity(q => Math.max(1, parseInt(q) - 1).toString())}
                    className="w-11 h-11 text-xl font-display flex items-center justify-center"
                    style={{ border: '1px solid rgba(255,255,255,0.09)', borderRadius: 4, background: 'rgba(255,255,255,0.04)', color: '#E8E8FF' }}>−</button>
                  <input type="number" value={quantity} onChange={e => setQuantity(e.target.value)} min="1"
                    aria-label={t.quantity}
                    className="flex-1 text-center text-lg font-mono text-foreground"
                    style={{ ...inputStyle, textAlign: 'center', padding: '12px' }} />
                  <button onClick={() => setQuantity(q => (parseInt(q) + 1).toString())}
                    className="w-11 h-11 text-xl font-display flex items-center justify-center"
                    style={{ border: '1px solid rgba(255,255,255,0.09)', borderRadius: 4, background: 'rgba(255,255,255,0.04)', color: '#E8E8FF' }}>+</button>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Preview */}
          {step === 3 && (
            <div className="flex flex-col gap-4 pt-2 animate-slide-up">
              <p className="font-pixel text-[8px] uppercase tracking-wider" style={{ color: '#FFD600' }}>{t.previewLabel}</p>

              {/* Preview card */}
              <div style={{ background: '#0C0E28', border: '1px solid rgba(255,214,0,0.3)', borderRadius: 6, overflow: 'hidden', boxShadow: '3px 3px 0 rgba(255,214,0,0.15)' }}>
                <div className="aspect-[2.5/1.5] flex items-center justify-center relative scanlines"
                  style={{ background: `linear-gradient(135deg, ${gradientFrom}33, ${gradientTo}55)` }}>
                  <span className="text-6xl">{typeIcon}</span>
                </div>
                <div className="p-4">
                  <h3 className="font-display font-bold text-foreground text-base">{productName || '—'}</h3>
                  <p className="text-muted-foreground text-sm font-mono mb-3">{set} · #{cardNumber}</p>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    {[
                      { label: t.condition, value: condition, color: conditionColor(condition) },
                      { label: t.language, value: cardLang.toUpperCase() },
                      { label: t.quantity, value: quantity },
                    ].map(d => (
                      <div key={d.label} className="p-2" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 3 }}>
                        <p className="font-display text-[10px] text-muted-foreground">{d.label}</p>
                        <p className="font-mono text-sm font-bold" style={{ color: d.color || '#E8E8FF' }}>{d.value}</p>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 pt-3 flex items-center justify-between" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                    <span className="font-display text-sm text-muted-foreground">{t.listedPrice}</span>
                    <span className="text-2xl font-bold font-mono" style={{ color: '#FFD600' }}>{currency === 'THB' ? '฿' : '$'}{parseFloat(price || '0').toLocaleString()}</span>
                  </div>
                </div>
              </div>

              <div className="p-3 flex gap-2 text-xs text-muted-foreground"
                style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 4 }}>
                <span>ℹ️</span><span>{t.negotiationNote}</span>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 pb-5 pt-3 shrink-0 flex gap-3" style={{ borderTop: '1px solid rgba(255,255,255,0.07)' }}>
          {step > 1 && (
            <button onClick={() => setStep(s => s - 1)}
              className="flex-1 py-3.5 text-sm font-bold font-display"
              style={{ border: '1px solid rgba(255,255,255,0.1)', borderRadius: 4, color: '#7880AA' }}>
              ← {t.back}
            </button>
          )}
          {step < totalSteps ? (
            <button onClick={() => setStep(s => s + 1)}
              disabled={step === 1 ? !canNext1 : !canNext2}
              className="flex-1 py-3.5 text-sm font-bold btn-primary transition-all"
              style={{ borderRadius: 4, opacity: (step === 1 ? canNext1 : canNext2) ? 1 : 0.4 }}>
              {t.next} →
            </button>
          ) : (
            <button onClick={() => {
              onSubmit({
                productName, set, cardNumber, condition, language: cardLang,
                listedPrice: parseFloat(price) || 0, currency, quantity: parseInt(quantity) || 1,
                typeIcon, gradientFrom, gradientTo,
                status: 'active', views: 0, likes: 0,
                createdAt: new Date().toISOString().split('T')[0],
                rarity: 'rare', setCode: cardNumber,
              });
              onClose();
            }} className="flex-1 py-3.5 text-sm font-bold btn-primary" style={{ borderRadius: 4 }}>
              ✓ {editListing ? t.save : t.createListing}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
