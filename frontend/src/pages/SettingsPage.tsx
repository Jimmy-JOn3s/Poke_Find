import { useState } from 'react';
import type { AppLang, Currency, ThemePreference, User } from '../types';
import { i18n } from '../i18n';
import LocaleCurrencySwitcher from '../components/LocaleCurrencySwitcher';
import ThemeSwitcher from '../components/ThemeSwitcher';

interface Props {
  lang: AppLang;
  onLangChange: (l: AppLang) => void;
  currency: Currency;
  onCurrencyChange: (currency: Currency) => void;
  theme: ThemePreference;
  onThemeChange: (theme: ThemePreference) => void;
  currentUser: User | null;
  isAuthenticated: boolean;
  onSignOut: () => void;
  onSignIn: () => void;
}

export default function SettingsPage({ lang, onLangChange, currency, onCurrencyChange, theme, onThemeChange, currentUser, isAuthenticated, onSignOut, onSignIn }: Props) {
  const t = i18n[lang];
  const [push, setPush] = useState(true);
  const [emailNotif, setEmailNotif] = useState(false);
  const [chatNotif, setChatNotif] = useState(true);
  const [priceAlert, setPriceAlert] = useState(false);

  const Toggle = ({ label, value, onChange }: { label: string; value: boolean; onChange: () => void }) => (
    <button type="button" aria-label={label} aria-pressed={value} onClick={onChange}
      className={`toggle shrink-0 ${value ? 'toggle-on' : 'toggle-off'}`}>
      <div className={`toggle-thumb ${value ? 'toggle-thumb-on' : 'toggle-thumb-off'}`} />
    </button>
  );

  const SectionHeader = ({ label }: { label: string }) => (
    <div className="px-4 py-2.5 panel-divider">
      <p className="font-pixel text-[8px] uppercase tracking-widest section-label">{label}</p>
    </div>
  );

  const Row = ({ icon, label, sublabel, right, onClick }: { icon: string; label: string; sublabel?: string; right?: React.ReactNode; onClick?: () => void }) => {
    const content = <>
      <span className="text-lg w-6 text-center shrink-0">{icon}</span>
      <div className="flex-1 min-w-0">
        <p className="font-display text-sm text-foreground">{label}</p>
        {sublabel && <p className="text-xs text-muted-foreground mt-0.5 leading-snug">{sublabel}</p>}
      </div>
      {right ?? (onClick && (
        <span className="text-xs text-muted-foreground shrink-0">›</span>
      ))}
    </>;
    const rowClass = "w-full min-w-0 flex items-center gap-3 px-4 py-3.5 text-left transition-colors panel-divider";
    return onClick
      ? <button type="button" onClick={onClick} className={`${rowClass} hover:bg-[var(--color-row-hover)]`}>{content}</button>
      : <div className={rowClass}>{content}</div>;
  };

  return (
    <div className="page-shell bg-background pixel-bg">
      <div className="page-container px-4 md:px-6 lg:px-8 page-header pb-4 shrink-0 page-header-bar">
        <h1 className="font-display text-xl font-bold page-title">{t.settingsTitle}</h1>
      </div>

      <div className="page-scroll scroll-end-buffer space-y-4 px-4 md:px-6 lg:px-8 pt-4 page-container max-w-2xl w-full">
        {/* Account */}
        {isAuthenticated && currentUser && (
          <div className="panel-card overflow-hidden">
            <div className="flex items-center gap-3 p-4 min-w-0 panel-divider">
              <div className="w-12 h-12 flex items-center justify-center text-lg font-bold shrink-0"
                style={{ background: 'linear-gradient(135deg, var(--color-secondary), var(--color-accent))', color: '#fff', borderRadius: 6, boxShadow: '2px 2px 0 var(--color-shadow-accent)' }}>
                {currentUser.avatar}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="font-display font-bold text-sm text-foreground truncate">{currentUser.name}</p>
                  {currentUser.role === 'business' && <span className="badge-business shrink-0">{t.businessBadge}</span>}
                </div>
                <p className="text-xs text-muted-foreground truncate">{currentUser.email}</p>
              </div>
            </div>
            <Row icon="👤" label={t.account} />
            <Row icon="🔒" label={t.security} />
            <Row icon={currentUser.verified ? '✅' : '🪪'} label={t.verification}
              sublabel={currentUser.verified ? t.verified : t.verifyToSell} />
          </div>
        )}

        {/* Appearance */}
        <div className="panel-card">
          <SectionHeader label={t.appearance} />
          <div className="p-4 pb-5">
            <ThemeSwitcher lang={lang} theme={theme} onThemeChange={onThemeChange} />
          </div>
        </div>

        {/* Notifications */}
        <div className="panel-card overflow-hidden">
          <SectionHeader label={t.notifications} />
          <Row icon="🔔" label={t.pushNotifications} sublabel={t.pushNotifSub} right={<Toggle label={t.pushNotifications} value={push} onChange={() => setPush(!push)} />} />
          <Row icon="📧" label={t.emailNotifications} sublabel={t.emailNotifSub} right={<Toggle label={t.emailNotifications} value={emailNotif} onChange={() => setEmailNotif(!emailNotif)} />} />
          <Row icon="💬" label={t.chatNotifications} sublabel={t.chatNotifSub} right={<Toggle label={t.chatNotifications} value={chatNotif} onChange={() => setChatNotif(!chatNotif)} />} />
          <Row icon="💰" label={t.priceAlerts} sublabel={t.priceAlertsSub} right={<Toggle label={t.priceAlerts} value={priceAlert} onChange={() => setPriceAlert(!priceAlert)} />} />
        </div>

        {/* Locale and currency */}
        <div className="panel-card">
          <SectionHeader label={t.appLanguage} />
          <div className="p-4 pb-5"><LocaleCurrencySwitcher lang={lang} currency={currency} onLangChange={onLangChange} onCurrencyChange={onCurrencyChange} /></div>
        </div>

        {/* Help + info */}
        <div className="panel-card overflow-hidden">
          <Row icon="❓" label={t.help} onClick={() => {}} />
          <Row icon="📄" label={t.privacy} onClick={() => {}} />
          <Row icon="📋" label={t.terms} onClick={() => {}} />
          <Row icon="ℹ️" label={t.version} right={<span className="text-xs text-muted-foreground font-mono">1.0.0</span>} />
        </div>

        {/* Sign out / in */}
        {isAuthenticated ? (
          <button onClick={onSignOut}
            className="w-full py-4 text-sm font-bold font-display transition-all btn-danger-outline">
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
