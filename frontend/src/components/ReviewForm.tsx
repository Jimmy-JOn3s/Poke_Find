import { useState } from "react";
import type { AppLang } from "../types";
import { i18n } from "../i18n";
import { api } from "../lib/api";

interface Props {
  lang: AppLang;
  dealId: number;
  revieweeName: string;
  onSubmitted: () => void;
  onCancel?: () => void;
}

export default function ReviewForm({ lang, dealId, revieweeName, onSubmitted, onCancel }: Props) {
  const t = i18n[lang];
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    setSubmitting(true);
    setError("");
    try {
      await api.submitReview(dealId, rating, comment.trim());
      onSubmitted();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Request failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-4 panel-card mb-3">
      <h3 className="font-display font-semibold text-sm text-foreground mb-1">
        {t.leaveReview} · {revieweeName}
      </h3>
      <p className="text-xs text-muted-foreground mb-3">{t.yourRating}</p>
      <div className="flex gap-1 mb-3">
        {Array.from({ length: 5 }).map((_, index) => (
          <button
            key={index}
            type="button"
            onClick={() => setRating(index + 1)}
            className="font-pixel text-xl leading-none"
            style={{ color: index < rating ? "var(--color-primary)" : "var(--color-star-inactive)" }}
            aria-label={`${index + 1} stars`}
          >
            ★
          </button>
        ))}
      </div>
      <label className="block text-xs text-muted-foreground mb-1">{t.reviewComment}</label>
      <textarea
        value={comment}
        onChange={event => setComment(event.target.value)}
        placeholder={t.reviewPlaceholder}
        rows={3}
        className="w-full field-input text-sm mb-3 resize-none"
      />
      {error && <p className="text-xs text-destructive mb-2">{error}</p>}
      <div className="flex gap-2">
        <button onClick={() => void submit()} disabled={submitting} className="flex-1 py-2 text-xs font-bold btn-primary">
          {submitting ? t.loading : t.submit}
        </button>
        {onCancel && (
          <button onClick={onCancel} className="px-4 py-2 text-xs btn-danger-outline">{t.cancel}</button>
        )}
      </div>
    </div>
  );
}
