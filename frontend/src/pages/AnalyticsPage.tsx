import type { AppLang, User } from '../types';
import { i18n } from '../i18n';

interface Props {
  lang: AppLang;
  currentUser: User | null;
  onBack: () => void;
}

export default function AnalyticsPage({ lang, currentUser, onBack }: Props) {
  const t = i18n[lang];

  if (!currentUser || currentUser.role !== 'business') {
    return (
      <div className="flex flex-col items-center justify-center h-full px-6 text-center pb-20 pixel-bg">
        <div className="text-5xl mb-4">🔒</div>
        <h2 className="font-display text-lg font-bold text-foreground mb-2">{t.businessOnly}</h2>
        <p className="text-muted-foreground text-sm mb-6">{lang === 'th' ? 'ฟีเจอร์นี้ใช้ได้เฉพาะบัญชีธุรกิจที่ยืนยันแล้ว' : 'This feature is only available for verified business accounts'}</p>
        <button onClick={onBack} className="px-6 py-3 text-sm font-bold font-display chip-btn-outline">
          {t.back}
        </button>
      </div>
    );
  }

  // Phase 1: analytics shows no numbers until real completed-deal data exists.
  // Placeholder/mock metrics were removed because fake numbers mislead real sellers.
  return (
    <div className="flex flex-col items-center justify-center h-full px-6 text-center pb-20 pixel-bg">
      <div className="text-5xl mb-4">📊</div>
      <h1 className="font-display text-lg font-bold text-foreground mb-2">{t.analyticsTitle}</h1>
      <div className="inline-block px-3 py-1 mb-3 text-xs font-bold font-display chip-btn-outline">{t.comingSoon}</div>
      <p className="text-muted-foreground text-sm mb-6 max-w-xs">{t.comingSoonHint}</p>
      <button onClick={onBack} className="px-6 py-3 text-sm font-bold font-display chip-btn-outline">
        {t.back}
      </button>
    </div>
  );
}
