import type { AppLang, User } from "../types";
import { i18n } from "../i18n";

interface Props {
  lang: AppLang;
  currentUser: User;
  onGoToSettings: () => void;
  onClose: () => void;
}

export default function VerifyIdentityListingModal({ lang, currentUser, onGoToSettings, onClose }: Props) {
  const t = i18n[lang];
  const pending = currentUser.verificationSubmission?.status === "pending";

  return (
    <div
      className="fixed inset-0 z-[90] flex items-end md:items-center justify-center p-0 md:p-4 modal-backdrop"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="w-full max-w-sm p-5 md:p-6 panel-card rounded-t-lg md:rounded-lg border-t md:border modal-panel"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-labelledby="verify-listing-title"
      >
        <div className="flex items-start gap-3 mb-4">
          <span className="text-3xl shrink-0" aria-hidden>
            🪪
          </span>
          <div>
            <h2 id="verify-listing-title" className="font-display text-lg font-bold text-foreground mb-1">
              {t.verifyIdentity}
            </h2>
            <p className="text-sm text-muted-foreground">{t.verifyIdentityBeforeListing}</p>
          </div>
        </div>

        {pending ? (
          <div className="p-3 mb-4 flex gap-2 text-xs text-muted-foreground detail-stat">
            <span aria-hidden>⏳</span>
            <span>
              <span className="font-semibold text-foreground">{t.pending}</span>
              {" — "}
              {t.pendingDesc}
            </span>
          </div>
        ) : (
          <p className="text-xs text-muted-foreground mb-4 p-3 detail-stat">{t.verificationDesc}</p>
        )}

        <div className="flex flex-col gap-2">
          {!pending && (
            <button type="button" onClick={onGoToSettings} className="w-full py-3 text-sm font-bold btn-primary">
              {t.completeVerification}
            </button>
          )}
          <button type="button" onClick={onClose} className="w-full py-2.5 text-sm text-muted-foreground">
            {t.skipForNow}
          </button>
        </div>
      </div>
    </div>
  );
}