import { useEffect, useState } from "react";
import type { AppLang } from "../types";
import { i18n } from "../i18n";
import { api, setTokens } from "../lib/api";
import type { MagicLink } from "../lib/magicLink";

interface Props {
  lang: AppLang;
  link: MagicLink;
  onSignedIn: () => void | Promise<void>;
}

export default function MagicLinkPage({ lang, link, onSignedIn }: Props) {
  const t = i18n[lang];
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const result = await api.confirmMagicLink(link.uid, link.token);
        setTokens({ access: result.access, refresh: result.refresh });
        if (!cancelled) onSignedIn();
      } catch (caught) {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Sign-in failed");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
    // Confirm once per link; onSignedIn is intentionally excluded to avoid duplicate requests.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- stable sign-in handler from App
  }, [link.uid, link.token]);

  return (
    <div className="flex flex-col min-h-full overflow-y-auto bg-background">
      <div className="px-5 pt-14 pb-8 max-w-md w-full mx-auto animate-slide-up text-center">
        <p className="font-pixel text-[10px] mb-3 text-accent" style={{ letterSpacing: "0.15em" }}>POKEFIND</p>
        {error ? (
          <>
            <p className="text-sm text-danger mb-4">{error}</p>
            <button onClick={onSignedIn} className="w-full py-3 text-sm font-bold btn-primary" style={{ borderRadius: 4 }}>
              {t.backToSignIn} →
            </button>
          </>
        ) : (
          <p className="text-sm text-muted-foreground">{t.magicLinkSigningIn}</p>
        )}
      </div>
    </div>
  );
}
