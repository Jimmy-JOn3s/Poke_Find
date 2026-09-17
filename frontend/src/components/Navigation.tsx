import type { Page, AppLang } from '../types';
import { i18n } from '../i18n';

interface Props {
  current: Page;
  onNav: (p: Page) => void;
  isAuthenticated: boolean;
  lang: AppLang;
  unreadChats: number;
}

type Tab = {
  id: Page;
  label: string;
  Icon: typeof DiscoverIcon;
  badge?: number;
};

export default function Navigation({ current, onNav, isAuthenticated, lang, unreadChats }: Props) {
  const t = i18n[lang];

  const tabs: Tab[] = [
    { id: 'discover', label: t.discover, Icon: DiscoverIcon },
    { id: 'chat', label: t.chat, Icon: ChatIcon, badge: unreadChats },
    { id: (isAuthenticated ? 'profile' : 'auth') as Page, label: isAuthenticated ? t.profile : t.signIn, Icon: ProfileIcon },
    { id: 'settings', label: t.settings, Icon: SettingsIcon },
  ];

  const isActive = (tab: Tab) =>
    current === tab.id ||
    (tab.id === 'auth' && current === 'auth') ||
    (tab.id === 'profile' && current === 'profile');

  const navStyle = {
    background: 'rgba(6,7,26,0.97)',
    backdropFilter: 'blur(24px)',
    borderColor: 'rgba(255,214,0,0.12)',
  };

  return (
    <>
      {/* Mobile: bottom tab bar */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 border-t" style={{ ...navStyle, boxShadow: '0 -2px 0 rgba(255,214,0,0.08)' }}>
        <div className="flex w-full max-w-lg mx-auto" style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}>
          {tabs.map(tab => (
            <NavButton key={tab.id} tab={tab} active={isActive(tab)} onNav={onNav} layout="mobile" />
          ))}
        </div>
      </nav>

      {/* Desktop: left sidebar */}
      <nav className="hidden md:flex fixed left-0 top-0 bottom-0 z-50 w-56 flex-col border-r" style={navStyle}>
        <div className="px-5 pt-6 pb-4 border-b" style={{ borderColor: 'rgba(255,214,0,0.1)' }}>
          <p className="font-pixel text-[9px] mb-1" style={{ color: '#FF2EBD', letterSpacing: '0.12em' }}>POKEFIND</p>
          <p className="font-display text-sm font-bold" style={{ color: '#FFD600', textShadow: '0 0 10px rgba(255,214,0,0.4)' }}>
            {t.discoverTitle}
          </p>
        </div>
        <div className="flex flex-col gap-1 p-3 flex-1">
          {tabs.map(tab => (
            <NavButton key={tab.id} tab={tab} active={isActive(tab)} onNav={onNav} layout="desktop" />
          ))}
        </div>
      </nav>
    </>
  );
}

function NavButton({ tab, active, onNav, layout }: { tab: Tab; active: boolean; onNav: (p: Page) => void; layout: 'mobile' | 'desktop' }) {
  if (layout === 'mobile') {
    return (
      <button onClick={() => onNav(tab.id)}
        className="flex-1 flex flex-col items-center gap-0.5 py-2.5 relative transition-all duration-150">
        {tab.badge ? (
          <span className="absolute top-2 right-[22%] w-4 h-4 rounded text-[9px] font-bold flex items-center justify-center z-10 font-pixel"
            style={{ background: '#FF2EBD', color: '#06071A', boxShadow: '1px 1px 0 rgba(180,0,100,0.6)' }}>
            {tab.badge > 9 ? '9+' : tab.badge}
          </span>
        ) : null}
        <tab.Icon active={active} />
        <span className="text-[9px] font-semibold tracking-wide transition-colors"
          style={{
            fontFamily: "'Chakra Petch', sans-serif",
            color: active ? '#FFD600' : '#5A6080',
            textShadow: active ? '0 0 8px rgba(255,214,0,0.6)' : 'none',
          }}>
          {tab.label}
        </span>
        {active && (
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-6 h-0.5"
            style={{ background: '#FFD600', boxShadow: '0 0 6px rgba(255,214,0,0.8)' }} />
        )}
      </button>
    );
  }

  return (
    <button onClick={() => onNav(tab.id)}
      className="flex items-center gap-3 px-3 py-2.5 rounded relative transition-all duration-150 text-left w-full"
      style={{
        background: active ? 'rgba(255,214,0,0.1)' : 'transparent',
        border: `1px solid ${active ? 'rgba(255,214,0,0.25)' : 'transparent'}`,
        boxShadow: active ? '2px 2px 0 rgba(255,214,0,0.1)' : 'none',
      }}>
      {tab.badge ? (
        <span className="absolute top-2 right-2 w-4 h-4 rounded text-[9px] font-bold flex items-center justify-center font-pixel"
          style={{ background: '#FF2EBD', color: '#06071A' }}>
          {tab.badge > 9 ? '9+' : tab.badge}
        </span>
      ) : null}
      <tab.Icon active={active} />
      <span className="text-sm font-semibold transition-colors"
        style={{
          fontFamily: "'Chakra Petch', sans-serif",
          color: active ? '#FFD600' : '#7880AA',
          textShadow: active ? '0 0 8px rgba(255,214,0,0.4)' : 'none',
        }}>
        {tab.label}
      </span>
    </button>
  );
}

function DiscoverIcon({ active }: { active: boolean }) {
  const c = active ? '#FFD600' : '#5A6080';
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
      <rect x="4" y="4" width="14" height="14" rx="2" stroke={c} strokeWidth={active ? 2 : 1.5} fill={active ? 'rgba(255,214,0,0.1)' : 'none'} />
      <circle cx="11" cy="11" r="3" stroke={c} strokeWidth={1.5} />
      <path d="M17 17L20 20" stroke={c} strokeWidth={active ? 2 : 1.5} strokeLinecap="square" />
    </svg>
  );
}

function ChatIcon({ active }: { active: boolean }) {
  const c = active ? '#FFD600' : '#5A6080';
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
      <path d="M4 4H20V16H6L2 20V4Z" fill={active ? 'rgba(255,214,0,0.1)' : 'none'} stroke={c} strokeWidth={active ? 2 : 1.5} strokeLinejoin="miter" />
      <line x1="7" y1="9" x2="17" y2="9" stroke={c} strokeWidth="1.5" strokeLinecap="square" />
      <line x1="7" y1="12" x2="13" y2="12" stroke={c} strokeWidth="1.5" strokeLinecap="square" />
    </svg>
  );
}

function ProfileIcon({ active }: { active: boolean }) {
  const c = active ? '#FFD600' : '#5A6080';
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
      <rect x="8" y="4" width="8" height="8" rx="1" stroke={c} strokeWidth={active ? 2 : 1.5} fill={active ? 'rgba(255,214,0,0.1)' : 'none'} />
      <path d="M4 20V19C4 16.8 7.6 15 12 15C16.4 15 20 16.8 20 19V20" stroke={c} strokeWidth={active ? 2 : 1.5} strokeLinecap="square" />
    </svg>
  );
}

function SettingsIcon({ active }: { active: boolean }) {
  const c = active ? '#FFD600' : '#5A6080';
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
      <rect x="9" y="9" width="6" height="6" stroke={c} strokeWidth={1.5} fill={active ? 'rgba(255,214,0,0.1)' : 'none'} />
      <path d="M12 2V6M12 18V22M2 12H6M18 12H22M4.93 4.93L7.76 7.76M16.24 16.24L19.07 19.07M19.07 4.93L16.24 7.76M7.76 16.24L4.93 19.07"
        stroke={c} strokeWidth={active ? 2 : 1.5} strokeLinecap="square" />
    </svg>
  );
}
