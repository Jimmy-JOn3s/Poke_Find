import { useEffect, useState } from "react";
import type { AppLang } from "../types";
import { i18n } from "../i18n";
import { api, mapUser } from "../lib/api";
import type { VerifyLink } from "../lib/verifyLink";

interface Props {
  lang: AppLang;
  link: VerifyLink;
  onVerified: (user?: ReturnType<typeof mapUser>) => void | Promise<void>;
}

export default function VerifyEmailPage({ lang, link, onVerified }: Props) {
  const t = i18n[lang];
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const result = await api.confirmEmailVerification(link.uid, link.token);
        if (!cancelled) {
          setDone(true);
          await onVerified(mapUser(result.user));
        }
      } catch (caught) {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Verification failed");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- confirm once per link
  }, [link.uid, link.token]);

  return (
    <div className="flex flex-col min-h-full overflow-y-auto bg-background">
      <div className="px-5 pt-14 pb-8 max-w-md w-full mx-auto animate-slide-up text-center">
        <p className="font-pixel text-[10px] mb-3 text-accent" style={{ letterSpacing: "0.15em" }}>POKEFIND</p>
        {error ? (
          <>
            <p className="text-sm text-danger mb-4">{error}</p>
            <button onClick={() => void onVerified()} className="w-full py-3 text-sm font-bold btn-primary" style={{ borderRadius: 4 }}>
              {t.backToSignIn} →
            </button>
          </>
        ) : done ? (
          <p className="text-sm text-success">✓ {t.emailVerifiedSuccess}</p>
        ) : (
          <p className="text-sm text-muted-foreground">{t.emailVerifying}</p>
        )}
      </div>
    </div>
  );
}
