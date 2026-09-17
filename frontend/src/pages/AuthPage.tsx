import { useState } from 'react';
import type { AppLang, UserRole } from '../types';
import { i18n } from '../i18n';

interface Props {
  lang: AppLang;
  onAuth: (role: UserRole, name: string, email: string, password: string, mode: 'signin' | 'signup') => Promise<void>;
  initialMode?: 'signin' | 'signup';
  error?: string;
  loading?: boolean;
}

export default function AuthPage({ lang, onAuth, initialMode = 'signin', error, loading }: Props) {
  const t = i18n[lang];
  const [mode, setMode] = useState<'signin' | 'signup'>(initialMode);
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState<UserRole>('personal');
  const [magicSent, setMagicSent] = useState(false);
  const [verifyType, setVerifyType] = useState<'id' | 'passport'>('id');
  const [frontUploaded, setFrontUploaded] = useState(false);
  const [backUploaded, setBackUploaded] = useState(false);
  const [verifySubmitted, setVerifySubmitted] = useState(false);

  const totalSteps = mode === 'signup' ? 3 : 1;

  const inputClass = 'field-input font-body text-sm';

  return (
    <div className="flex flex-col md:flex-row min-h-full overflow-y-auto bg-background">
      {/* Hero */}
      <div className="relative overflow-hidden pt-14 md:pt-0 pb-8 md:pb-0 px-6 md:px-10 lg:px-16 text-center md:text-left pixel-bg md:w-2/5 lg:w-5/12 shrink-0 flex items-center profile-hero">
        <div className="absolute inset-0 profile-hero-glow" />
        <div className="relative md:max-w-sm">
          <p className="font-pixel text-[10px] mb-3 text-accent" style={{ letterSpacing: '0.15em' }}>POKEFIND</p>
          <div className="text-5xl md:text-6xl mb-2" style={{ filter: 'drop-shadow(0 0 16px rgba(255,214,0,0.6))' }}>⚡</div>
          <h1 className="font-display text-2xl md:text-3xl font-bold text-foreground">
            {mode === 'signin' ? t.welcomeBack : t.createAccount}
          </h1>
          <p className="text-muted-foreground text-sm mt-1 md:mt-2">
            {lang === 'th' ? 'ตลาดซื้อขายการ์ด Pokémon ที่น่าเชื่อถือ' : 'Thailand\'s trusted Pokémon card marketplace'}
          </p>
        </div>
      </div>

      <div className="flex-1 flex flex-col min-w-0 md:justify-center md:px-8 lg:px-12 md:py-8">
      {/* Progress dots */}
      {mode === 'signup' && (
        <div className="flex justify-center md:justify-start gap-2 py-3 px-5 md:px-0">
          {Array.from({ length: totalSteps }).map((_, i) => (
            <div key={i} className="h-1.5 transition-all duration-300"
              style={{ width: step === i + 1 ? 24 : 8, background: step > i ? 'var(--color-primary)' : 'var(--color-toggle-off)', borderRadius: 1 }} />
          ))}
        </div>
      )}

      <div className="flex-1 md:flex-none px-5 md:px-0 pb-8 md:pb-0 bottom-safe max-w-md md:max-w-lg w-full md:mx-0">
        {/* Step 1: Credentials */}
        {step === 1 && (
          <div className="animate-slide-up">
            {/* Mode toggle */}
            <div className="flex overflow-hidden mb-5 mt-2 border border-border" style={{ borderRadius: 4 }}>
              {(['signin', 'signup'] as const).map(m => (
                <button key={m} onClick={() => { setMode(m); setStep(1); setMagicSent(false); }}
                  className={`flex-1 py-2.5 text-sm font-bold transition-all font-display ${mode === m ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'}`}
                  style={{ boxShadow: mode === m ? 'inset 2px 2px 0 var(--color-shadow-pixel)' : 'none' }}>
                  {m === 'signin' ? t.signIn : t.createAccount}
                </button>
              ))}
            </div>

            {/* Google */}
            <button disabled title={lang === 'th' ? 'จะเพิ่มในเวอร์ชันถัดไป' : 'Planned for a later release'}
              className={`${inputClass} flex items-center justify-center gap-3 py-3 mb-3 opacity-45`}>
              <GoogleIcon /> {t.continueWithGoogle}
            </button>

            <div className="flex items-center gap-3 mb-3">
              <div className="flex-1 h-px bg-border" />
              <span className="text-xs text-muted-foreground">{t.or}</span>
              <div className="flex-1 h-px bg-border" />
            </div>

            {mode === 'signup' && (
              <input type="text" value={name} onChange={e => setName(e.target.value)}
                aria-label={t.fullName}
                placeholder={t.fullName} className={`${inputClass} mb-3 block`} />
            )}

            <input type="email" value={email} onChange={e => setEmail(e.target.value)}
              aria-label={t.email} autoComplete="email"
              placeholder={t.email} className={`${inputClass} mb-3 block`} />

            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
              aria-label={t.password} autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
              placeholder={t.password} className={`${inputClass} mb-3 block`} />

            {error && <p className="text-xs mb-3 text-danger">{error}</p>}

            {!magicSent ? (
              <button onClick={() => { if (email) setMagicSent(true); }}
                className="w-full py-3 text-sm font-semibold mb-2 transition-all"
                style={{ background: 'rgba(255,214,0,0.1)', border: '1px solid rgba(255,214,0,0.35)', borderRadius: 4, color: '#FFD600', fontFamily: "'Chakra Petch', sans-serif" }}>
                ✉ {t.magicLink}
              </button>
            ) : (
              <div className="w-full py-3.5 text-sm text-center mb-2"
                style={{ background: 'rgba(0,230,118,0.08)', border: '1px solid rgba(0,230,118,0.3)', borderRadius: 4, color: '#00E676' }}>
                ✓ {t.linkSentTo} {email || 'อีเมล'}
              </div>
            )}

            <button disabled={loading || !email || password.length < 8}
              onClick={() => mode === 'signup' ? setStep(2) : void onAuth('personal', name || (lang === 'th' ? 'ผู้ใช้' : 'User'), email, password, 'signin')}
              className="w-full py-3 text-sm font-bold btn-primary"
              style={{ borderRadius: 4, marginTop: 4, opacity: loading || !email || password.length < 8 ? 0.45 : 1 }}>
              {loading ? t.loading : mode === 'signin' ? t.signIn : `${t.next} →`}
            </button>
          </div>
        )}

        {/* Step 2: Role */}
        {step === 2 && (
          <div className="animate-slide-up">
            <h2 className="font-display text-lg font-bold text-foreground mb-1">{t.chooseRole}</h2>
            <p className="text-muted-foreground text-sm mb-5">{lang === 'th' ? 'เลือกประเภทบัญชีที่เหมาะกับคุณ' : 'Choose the account type that fits you'}</p>

            {(['personal', 'business'] as UserRole[]).map(r => (
              <button key={r} onClick={() => setRole(r)}
                className={`w-full flex items-start gap-4 p-4 text-left mb-3 transition-all panel-card ${role === r ? 'surface-subtle' : ''}`}
                style={{ boxShadow: role === r ? '3px 3px 0 color-mix(in srgb, var(--color-primary) 20%, transparent)' : 'none' }}>
                <div className="text-3xl mt-0.5">{r === 'personal' ? '👤' : '🏪'}</div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="font-display font-semibold text-sm text-foreground">
                      {r === 'personal' ? t.personalAccount : t.businessAccount}
                    </span>
                    {role === r && <span className="font-pixel text-[8px] px-1.5 py-0.5 bg-primary text-primary-foreground" style={{ borderRadius: 2 }}>✓</span>}
                  </div>
                  <p className="text-xs text-muted-foreground">{r === 'personal' ? t.personalDesc : t.businessDesc}</p>
                  {r === 'business' && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {[t.analyticsTitle, lang === 'th' ? 'จัดการสต็อก' : 'Inventory', lang === 'th' ? 'รายงาน' : 'Reports'].map(f => (
                        <span key={f} className="text-[10px] px-2 py-0.5" style={{ border: '1px solid rgba(255,214,0,0.25)', color: '#FFD600', borderRadius: 2 }}>{f}</span>
                      ))}
                    </div>
                  )}
                </div>
              </button>
            ))}

            <button onClick={() => setStep(3)} className="w-full py-3 text-sm font-bold btn-primary mt-2" style={{ borderRadius: 4 }}>
              {t.next} →
            </button>
          </div>
        )}

        {/* Step 3: Verification */}
        {step === 3 && (
          <div className="animate-slide-up">
            <h2 className="font-display text-lg font-bold text-foreground mb-1">{t.verification}</h2>
            <p className="text-muted-foreground text-sm mb-5">{t.verificationDesc}</p>

            {!verifySubmitted ? (
              <>
                <div className="flex gap-2 mb-4">
                  {(['id', 'passport'] as const).map(type => (
                    <button key={type} onClick={() => setVerifyType(type)}
                      className={`flex-1 py-2.5 text-sm font-semibold transition-all font-display chip-btn ${verifyType === type ? 'chip-btn-active' : ''}`}>
                      {type === 'id' ? `🪪 ${t.idCard}` : `📗 ${t.passport}`}
                    </button>
                  ))}
                </div>

                <div className="grid grid-cols-2 gap-3 mb-4">
                  {[
                    { label: t.uploadFront, done: frontUploaded, onUp: () => setFrontUploaded(true) },
                    ...(verifyType === 'id' ? [{ label: t.uploadBack, done: backUploaded, onUp: () => setBackUploaded(true) }] : []),
                  ].map(u => (
                    <button key={u.label} onClick={u.onUp}
                      className="aspect-[4/3] flex flex-col items-center justify-center gap-2 text-center p-3 transition-all"
                      style={{
                        border: `2px dashed ${u.done ? 'color-mix(in srgb, var(--color-success) 50%, transparent)' : 'var(--color-border)'}`,
                        borderRadius: 4,
                        background: u.done ? 'color-mix(in srgb, var(--color-success) 6%, transparent)' : 'var(--color-muted)',
                      }}>
                      <div className="text-2xl">{u.done ? '✅' : '📷'}</div>
                      <span className="text-xs text-muted-foreground">{u.done ? t.uploaded : u.label}</span>
                    </button>
                  ))}
                </div>

                <div className="p-3 mb-5 flex gap-2 text-xs text-muted-foreground detail-stat">
                  <span>🔒</span><span>{t.secureNote}</span>
                </div>

                <button onClick={() => frontUploaded && setVerifySubmitted(true)}
                  className="w-full py-3 text-sm font-bold mb-2 btn-primary"
                  style={{ borderRadius: 4, opacity: frontUploaded ? 1 : 0.4, cursor: frontUploaded ? 'pointer' : 'default' }}>
                  {t.completeVerification}
                </button>
                <button onClick={() => void onAuth(role, name || (lang === 'th' ? 'ผู้ใช้ใหม่' : 'New User'), email, password, 'signup')}
                  className="w-full py-2.5 text-sm text-muted-foreground" style={{ fontFamily: "'Sarabun', sans-serif" }}>
                  {t.skipForNow}
                </button>
              </>
            ) : (
              <div className="flex flex-col items-center py-8">
                <div className="text-5xl mb-4">⏳</div>
                <h3 className="font-display text-lg font-bold text-foreground mb-2">{t.pending}</h3>
                <p className="text-muted-foreground text-sm text-center mb-6">{t.pendingDesc}</p>
                <button onClick={() => void onAuth(role, name || (lang === 'th' ? 'ผู้ใช้ใหม่' : 'New User'), email, password, 'signup')}
                  className="px-8 py-3 text-sm font-bold btn-primary" style={{ borderRadius: 4 }}>
                  {t.startUsing} →
                </button>
              </div>
            )}
          </div>
        )}
      </div>
      </div>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
    </svg>
  );
}
