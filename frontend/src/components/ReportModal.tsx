import { useState } from "react";
import type { AppLang } from "../types";
import { i18n } from "../i18n";
import { api, type ReportReason } from "../lib/api";

export type ReportTarget =
  | { category: "listing"; listingId: string; label: string }
  | { category: "user"; reportedUserId: string; label: string };

interface Props {
  lang: AppLang;
  target: ReportTarget;
  isAuthenticated: boolean;
  onClose: () => void;
  onSignIn: () => void;
}

const REASONS: { value: ReportReason; labelKey: keyof typeof i18n.en }[] = [
  { value: "spam", labelKey: "reportReasonSpam" },
  { value: "scam", labelKey: "reportReasonScam" },
  { value: "fake_listing", labelKey: "reportReasonFakeListing" },
  { value: "harassment", labelKey: "reportReasonHarassment" },
  { value: "inappropriate", labelKey: "reportReasonInappropriate" },
  { value: "other", labelKey: "reportReasonOther" },
];

export default function ReportModal({ lang, target, isAuthenticated, onClose, onSignIn }: Props) {
  const t = i18n[lang];
  const [reason, setReason] = useState<ReportReason>("scam");
  const [details, setDetails] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  const title = target.category === "listing" ? t.reportListing : t.reportUser;

  const submit = async () => {
    if (!isAuthenticated) {
      onSignIn();
      return;
    }
    setLoading(true);
    setError("");
    try {
      await api.submitReport({
        category: target.category,
        reason,
        details,
        listing_id: target.category === "listing" ? Number(target.listingId) : undefined,
        reported_user_id: target.category === "user" ? Number(target.reportedUserId) : undefined,
      });
      setDone(true);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not submit report");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center animate-fade-in p-0 md:p-4 modal-backdrop">
      <div className="w-full max-w-lg p-5 border-t md:border rounded-t-lg md:rounded-lg modal-panel max-h-[90vh] overflow-y-auto">
        <h3 className="font-display text-lg font-bold text-foreground mb-1">{title}</h3>
        <p className="text-xs text-muted-foreground mb-4 truncate">{target.label}</p>

        {!isAuthenticated ? (
          <>
            <p className="text-sm text-muted-foreground mb-5">{t.reportSignIn}</p>
            <div className="flex gap-3">
              <button type="button" onClick={onClose} className="flex-1 py-3 text-sm font-bold font-display chip-btn-outline">{t.cancel}</button>
              <button type="button" onClick={onSignIn} className="flex-1 py-3 text-sm font-bold font-display btn-primary" style={{ borderRadius: 4 }}>{t.signIn}</button>
            </div>
          </>
        ) : done ? (
          <>
            <p className="text-sm text-success mb-5">{t.reportSubmitted}</p>
            <button type="button" onClick={onClose} className="w-full py-3 text-sm font-bold font-display btn-primary" style={{ borderRadius: 4 }}>{t.confirm}</button>
          </>
        ) : (
          <>
            <label className="block mb-3">
              <span className="font-display text-xs text-muted-foreground">{t.reportReason}</span>
              <select value={reason} onChange={event => setReason(event.target.value as ReportReason)}
                className="mt-1 w-full px-3 py-2.5 text-sm bg-background border border-border rounded font-display">
                {REASONS.map(option => (
                  <option key={option.value} value={option.value}>{t[option.labelKey]}</option>
                ))}
              </select>
            </label>
            <label className="block mb-4">
              <span className="font-display text-xs text-muted-foreground">{t.reportDetails}</span>
              <textarea value={details} onChange={event => setDetails(event.target.value)} maxLength={2000} rows={4}
                placeholder={t.reportDetailsPlaceholder}
                className="mt-1 w-full px-3 py-2.5 text-sm bg-background border border-border rounded resize-none font-display" />
            </label>
            {error && <p className="text-xs text-danger mb-3">{error}</p>}
            <div className="flex gap-3">
              <button type="button" onClick={onClose} disabled={loading}
                className="flex-1 py-3 text-sm font-bold font-display chip-btn-outline">{t.cancel}</button>
              <button type="button" onClick={() => void submit()} disabled={loading}
                className="flex-1 py-3 text-sm font-bold font-display btn-danger-outline">{loading ? t.loading : t.reportSubmit}</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
