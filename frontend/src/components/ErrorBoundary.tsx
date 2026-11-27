import { Component, type ErrorInfo, type ReactNode } from "react";
import { i18n } from "../i18n";

interface State { failed: boolean }

/** Reading storage can itself throw (blocked site data, some webviews), and that may be why the app crashed. */
function storedLanguage(): "th" | "en" {
  try {
    return localStorage.getItem("pokefind.language") === "en" ? "en" : "th";
  } catch {
    return "th";
  }
}

/** Catches a crash while rendering so the user gets a way back instead of a blank screen. */
export default class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { failed: false };

  static getDerivedStateFromError(): State {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("PokeFind crashed while rendering", error, info.componentStack);
  }

  render() {
    if (!this.state.failed) return this.props.children;
    const t = i18n[storedLanguage()];
    return (
      <div role="alert" className="flex flex-col items-center justify-center min-h-screen px-5 text-center bg-background">
        <p className="font-pixel text-[10px] mb-3 text-accent" style={{ letterSpacing: "0.15em" }}>POKEFIND</p>
        <p className="text-base font-bold mb-1">{t.appCrashed}</p>
        <p className="text-sm text-muted-foreground mb-5">{t.appCrashedHint}</p>
        <button onClick={() => window.location.reload()} className="px-6 py-3 text-sm font-bold btn-primary" style={{ borderRadius: 4 }}>
          {t.reloadPage}
        </button>
      </div>
    );
  }
}
