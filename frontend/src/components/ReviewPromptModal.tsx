import type { AppLang } from "../types";
import { i18n } from "../i18n";

interface Props {
  lang: AppLang;
  revieweeName: string;
  onLeaveReview: () => void;
  onDismiss: () => void;
}

export default function ReviewPromptModal({ lang, revieweeName, onLeaveReview, onDismiss }: Props) {
  const t = i18n[lang];

  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center p-4"
      style={{ background: "color-mix(in srgb, var(--color-background) 20%, rgba(0,0,0,0.55))" }}>
      <div className="w-full max-w-sm p-6 text-center panel-card" style={{ borderRadius: 8 }}>
        <div className="text-4xl mb-3">⭐</div>
        <h2 className="font-display text-lg font-bold text-foreground mb-2">{t.reviewPromptTitle}</h2>
        <p className="text-sm text-muted-foreground mb-1">{t.reviewPromptBody}</p>
        <p className="text-sm font-semibold text-primary mb-6">{t.reviewFor} {revieweeName}</p>
        <div className="flex flex-col gap-2">
          <button onClick={onLeaveReview} className="w-full py-3 text-sm font-bold btn-primary">
            {t.leaveReview}
          </button>
          <button onClick={onDismiss} className="w-full py-2 text-xs text-muted-foreground">
            {t.reviewLater}
          </button>
        </div>
      </div>
    </div>
  );
}
