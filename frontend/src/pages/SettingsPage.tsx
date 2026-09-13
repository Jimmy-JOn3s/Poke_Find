import { useState } from 'react';
import type { AppLang, Currency, User } from '../types';
import { i18n } from '../i18n';
import LocaleCurrencySwitcher from '../components/LocaleCurrencySwitcher';

interface Props {
  lang: AppLang;
  onLangChange: (l: AppLang) => void;
  currency: Currency;
  onCurrencyChange: (currency: Currency) => void;
  currentUser: User | null;
  isAuthenticated: boolean;
  onSignOut: () => void;
  onSignIn: () => void;
}

export default function SettingsPage({ lang, onLangChange, currency, onCurrencyChange, currentUser, isAuthenticated, onSignOut, onSignIn }: Props) {
  const t = i18n[lang];
  const [push, setPush] = useState(true);
  const [emailNotif, setEmailNotif] = useState(false);
  const [chatNotif, setChatNotif] = useState(true);
  const [priceAlert, setPriceAlert] = useState(false);

  const Toggle = ({ label, value, onChange }: { label: string; value: boolean; onChange: () => void }) => (
    <button type="button" aria-label={label} aria-pressed={value} onClick={onChange} className="toggle shrink-0" style={{ background: value ? '#FFD600' : 'rgba(255,255,255,0.12)' }}>
      <div className="toggle-thumb" style={{ left: value ? 'calc(100% - 20px)' : '3px', background: value ? '#06071A' : 'white' }} />
    </button>
  );

  const SectionHeader = ({ label }: { label: string }) => (
    <div className="px-4 py-2.5" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
      <p className="font-pixel text-[8px] uppercase tracking-widest" style={{ color: '#FFD600' }}>{label}</p>
    </div>
  );

  const Row = ({ icon, label, sublabel, right, onClick }: { icon: string; label: string; sublabel?: string; right?: React.ReactNode; onClick?: () => void }) => {
    const content = <>
      <span className="text-lg w-6 text-center shrink-0">{icon}</span>
      <div className="flex-1">
        <p className="font-display text-sm text-foreground">{label}</p>
        {sublabel && <p className="text-xs text-muted-foreground mt-0.5">{sublabel}</p>}
      </div>
      {right ?? (onClick && (
        <span className="text-xs text-muted-foreground">›</span>
      ))}
    </>;
    const rowClass = "w-full flex items-center gap-3 px-4 py-3.5 text-left transition-colors";
    const rowStyle = { borderBottom: '1px solid rgba(255,255,255,0.05)' };
    return onClick
      ? <button type="button" onClick={onClick} className={`${rowClass} hover:bg-white/[0.03]`} style={rowStyle}>{content}</button>
      : <div className={rowClass} style={rowStyle}>{content}</div>;
  };

  return (
    <div className="flex flex-col min-h-full bg-background pixel-bg">
      <div className="px-4 pt-12 pb-4 shrink-0"
        style={{ position: 'sticky', top: 0, zIndex: 10, background: 'rgba(6,7,26,0.97)', backdropFilter: 'blur(20px)', borderBottom: '1px solid rgba(255,214,0,0.1)' }}>
        <h1 className="font-display text-xl font-bold" style={{ color: '#FFD600', textShadow: '0 0 12px rgba(255,214,0,0.4)' }}>{t.settingsTitle}</h1>
      </div>

      <div className="flex-1 overflow-y-auto pb-6 bottom-safe flex flex-col gap-4 px-4 pt-4">
        {/* Account */}
        {isAuthenticated && currentUser && (
          <div style={{ background: '#0C0E28', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 6, overflow: 'hidden' }}>
            <div className="flex items-center gap-3 p-4" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
              <div className="w-12 h-12 flex items-center justify-center text-lg font-bold shrink-0"
                style={{ background: 'linear-gradient(135deg, #3B1874, #FF2EBD)', color: '#fff', borderRadius: 6, boxShadow: '2px 2px 0 rgba(255,46,189,0.3)' }}>
                {currentUser.avatar}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <p className="font-display font-bold text-sm text-foreground">{currentUser.name}</p>
                  {currentUser.role === 'business' && <span className="badge-business">{t.businessBadge}</span>}
                </div>
                <p className="text-xs text-muted-foreground">{currentUser.email}</p>
              </div>
            </div>
            <Row icon="👤" label={t.account} />
            <Row icon="🔒" label={t.security} />
            <Row icon={currentUser.verified ? '✅' : '🪪'} label={t.verification}
              sublabel={currentUser.verified ? t.verified : t.verifyToSell} />
          </div>
        )}

        {/* Notifications */}
        <div style={{ background: '#0C0E28', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 6, overflow: 'hidden' }}>
          <SectionHeader label={t.notifications} />
          <Row icon="🔔" label={t.pushNotifications} sublabel={t.pushNotifSub} right={<Toggle label={t.pushNotifications} value={push} onChange={() => setPush(!push)} />} />
          <Row icon="📧" label={t.emailNotifications} sublabel={t.emailNotifSub} right={<Toggle label={t.emailNotifications} value={emailNotif} onChange={() => setEmailNotif(!emailNotif)} />} />
          <Row icon="💬" label={t.chatNotifications} sublabel={t.chatNotifSub} right={<Toggle label={t.chatNotifications} value={chatNotif} onChange={() => setChatNotif(!chatNotif)} />} />
          <Row icon="💰" label={t.priceAlerts} sublabel={t.priceAlertsSub} right={<Toggle label={t.priceAlerts} value={priceAlert} onChange={() => setPriceAlert(!priceAlert)} />} />
        </div>

        {/* Locale and currency */}
        <div style={{ background: '#0C0E28', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 6, overflow: 'hidden' }}>
          <SectionHeader label={t.appLanguage} />
          <div className="p-3"><LocaleCurrencySwitcher lang={lang} currency={currency} onLangChange={onLangChange} onCurrencyChange={onCurrencyChange} /></div>
        </div>

        {/* Help + info */}
        <div style={{ background: '#0C0E28', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 6, overflow: 'hidden' }}>
          <Row icon="❓" label={t.help} onClick={() => {}} />
          <Row icon="📄" label={t.privacy} onClick={() => {}} />
          <Row icon="📋" label={t.terms} onClick={() => {}} />
          <Row icon="ℹ️" label={t.version} right={<span className="text-xs text-muted-foreground font-mono">1.0.0</span>} />
        </div>

        {/* Sign out / in */}
        {isAuthenticated ? (
          <button onClick={onSignOut}
            className="w-full py-4 text-sm font-bold font-display transition-all"
            style={{ border: '1px solid rgba(255,61,87,0.3)', color: '#FF3D57', background: 'rgba(255,61,87,0.06)', borderRadius: 4 }}>
            ← {t.signOut}
          </button>
        ) : (
          <button onClick={onSignIn}
            className="w-full py-4 text-sm font-bold btn-primary" style={{ borderRadius: 4 }}>
            {t.signIn}
          </button>
        )}
      </div>
    </div>
  );
}
