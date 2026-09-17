import type { AppLang } from "../types";
import type { ThemePreference } from "../lib/theme";
import { i18n } from "../i18n";

interface Props {
  lang: AppLang;
  theme: ThemePreference;
  onThemeChange: (theme: ThemePreference) => void;
}

const OPTIONS: { value: ThemePreference; icon: string; labelKey: keyof typeof i18n.en }[] = [
  { value: "light", icon: "☀️", labelKey: "lightMode" },
  { value: "dark", icon: "🌙", labelKey: "darkMode" },
  { value: "system", icon: "💻", labelKey: "systemTheme" },
];

export default function ThemeSwitcher({ lang, theme, onThemeChange }: Props) {
  const t = i18n[lang];

  return (
    <div className="theme-segment" role="group" aria-label={t.appearance}>
      {OPTIONS.map(option => (
        <button
          key={option.value}
          type="button"
          className="theme-segment-btn"
          aria-pressed={theme === option.value}
          onClick={() => onThemeChange(option.value)}
        >
          <span className="theme-segment-icon" aria-hidden="true">{option.icon}</span>
          <span>{t[option.labelKey]}</span>
        </button>
      ))}
    </div>
  );
}
