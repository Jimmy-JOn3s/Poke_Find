import { useEffect, useState } from "react";
import type { AppLang, Currency, Listing, Page, ReviewContext, ThemePreference, User, UserRole } from "./types";
import { applyTheme, storedTheme, THEME_STORAGE_KEY } from "./lib/theme";
import Navigation from "./components/Navigation";
import CreateListingModal from "./components/CreateListingModal";
import DiscoverPage from "./pages/DiscoverPage";
import AuthPage from "./pages/AuthPage";
import ListingDetailPage from "./pages/ListingDetailPage";
import ChatPage from "./pages/ChatPage";
import ProfilePage from "./pages/ProfilePage";
import SettingsPage from "./pages/SettingsPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import AdminPage from "./pages/AdminPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import MagicLinkPage from "./pages/MagicLinkPage";
import VerifyEmailPage from "./pages/VerifyEmailPage";
import { i18n } from "./i18n";
import { api, mapListing, mapUser, setTokens } from "./lib/api";
import { useListings } from "./hooks/useListings";
import { readMagicLink } from "./lib/magicLink";
import { readResetLink } from "./lib/resetLink";
import { readVerifyLink } from "./lib/verifyLink";


function storedPreference<T extends string>(key: string, fallback: T): T {
  return (localStorage.getItem(key) as T | null) || fallback;
}


export default function App() {
  const [lang, setLangState] = useState<AppLang>(() => storedPreference("pokefind.language", "th"));
  const [currency, setCurrencyState] = useState<Currency>(() => storedPreference("pokefind.currency", "THB"));
  const [theme, setThemeState] = useState<ThemePreference>(() => storedTheme());
  // A password-reset email opens the app with the token in the URL fragment (see backend/accounts/password_reset.py).
  const [resetLink, setResetLink] = useState(() => readResetLink(window.location.hash));
  const [magicLink, setMagicLink] = useState(() => readMagicLink(window.location.hash));
  const [verifyLink, setVerifyLink] = useState(() => readVerifyLink(window.location.hash));
  const [currentPage, setCurrentPage] = useState<Page>(() => {
    if (resetLink) return "resetPassword";
    if (magicLink) return "magicLink";
    if (verifyLink) return "verifyEmail";
    return "discover";
  });
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null);
  const [viewUserId, setViewUserId] = useState<string | undefined>();
  const [reviewContext, setReviewContext] = useState<ReviewContext | undefined>();
  const [showCreateListing, setShowCreateListing] = useState(false);
  const [editListing, setEditListing] = useState<Listing | undefined>();
  const [authError, setAuthError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [actionError, setActionError] = useState("");
  const { listings, loading, error, reload, create, remove, setListings } = useListings();

  const isAuthenticated = Boolean(currentUser);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  useEffect(() => {
    // Also handle a reset link opened in a tab that already shows the app: only the fragment changes, so
    // the page doesn't reload.
    const openAuthLink = () => {
      const reset = readResetLink(window.location.hash);
      const magic = readMagicLink(window.location.hash);
      const verify = readVerifyLink(window.location.hash);
      if (reset) {
        setResetLink(reset);
        setMagicLink(null);
        setVerifyLink(null);
        setCurrentPage("resetPassword");
      } else if (magic) {
        setMagicLink(magic);
        setResetLink(null);
        setVerifyLink(null);
        setCurrentPage("magicLink");
      } else if (verify) {
        setVerifyLink(verify);
        setResetLink(null);
        setMagicLink(null);
        setCurrentPage("verifyEmail");
      } else {
        return;
      }
      // Drop the token from the address bar and the history entry as soon as it has been read.
      window.history.replaceState(null, "", window.location.pathname + window.location.search);
    };
    openAuthLink();
    window.addEventListener("hashchange", openAuthLink);
    return () => window.removeEventListener("hashchange", openAuthLink);
  }, []);

  useEffect(() => {
    if (theme !== "system") return;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => applyTheme("system");
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [theme]);

  useEffect(() => {
    api.me().then(user => {
      const mapped = mapUser(user);
      setCurrentUser(mapped);
      if (mapped.preferredLanguage) setLangState(mapped.preferredLanguage);
      if (mapped.preferredCurrency) setCurrencyState(mapped.preferredCurrency);
    }).catch(() => undefined);
  }, []);

  const setLang = (next: AppLang) => {
    setLangState(next);
    localStorage.setItem("pokefind.language", next);
    if (isAuthenticated) void api.updateMe({ preferred_language: next });
  };

  const setCurrency = (next: Currency) => {
    setCurrencyState(next);
    localStorage.setItem("pokefind.currency", next);
    if (isAuthenticated) void api.updateMe({ preferred_currency: next });
  };

  const setTheme = (next: ThemePreference) => {
    setThemeState(next);
    localStorage.setItem(THEME_STORAGE_KEY, next);
    applyTheme(next);
  };

  const handleAuth = async (
    role: UserRole, name: string, email: string, password: string, mode: "signin" | "signup",
    options?: { deferNavigation?: boolean },
  ) => {
    setAuthLoading(true);
    setAuthError("");
    try {
      if (mode === "signup") {
        const usernameBase = email.split("@")[0].replace(/[^a-zA-Z0-9_-]/g, "-") || "trainer";
        const result = await api.register({
          username: `${usernameBase}-${Date.now().toString().slice(-5)}`, email, password,
          display_name: name, role, preferred_language: lang, preferred_currency: currency,
        });
        setTokens({ access: result.access, refresh: result.refresh });
        setCurrentUser(mapUser(result.user));
      } else {
        const result = await api.login(email, password);
        setTokens(result);
        setCurrentUser(mapUser(await api.me()));
      }
      if (!options?.deferNavigation) setCurrentPage("discover");
      await reload();
    } catch (caught) {
      setAuthError(caught instanceof Error ? caught.message : "Authentication failed");
      throw caught;
    } finally {
      setAuthLoading(false);
    }
  };

  const handleSignOut = () => {
    void api.logout();
    setCurrentUser(null);
    setCurrentPage("discover");
    void reload();
  };

  const handleNav = (page: Page) => {
    setConversationId(null);
    setSelectedListing(null);
    setViewUserId(undefined);
    setReviewContext(undefined);
    setCurrentPage(page);
  };

  const handleLeaveReview = (context: ReviewContext) => {
    setReviewContext(context);
    setViewUserId(context.revieweeId);
    setCurrentPage("profile");
  };

  const handleCreateListing = async (data: Partial<Listing>, photoFile?: File | null) => {
    setActionError("");
    const payload = {
      product_name: data.productName, set_name: data.set, set_code: data.setCode,
      card_number: data.cardNumber, condition: data.condition, card_language: data.language,
      rarity: data.rarity || "rare", asking_price: String(data.listedPrice), currency: data.currency || currency,
      quantity: data.quantity || 1, description: data.description || "",
    };
    try {
      if (editListing) {
        // Edits never send status: once a card is reserved or sold, the deal flow owns it.
        const updated = mapListing(await api.updateListing(editListing.id, payload, photoFile));
        setListings(current => current.map(item => item.id === updated.id ? updated : item));
        if (selectedListing?.id === updated.id) setSelectedListing(updated);
      } else {
        await create({ ...payload, status: "active" }, photoFile);
      }
      setShowCreateListing(false);
      setEditListing(undefined);
    } catch (caught) {
      setActionError(caught instanceof Error ? caught.message : "Could not save listing");
    }
  };

  const handleDeleteListing = async (listingId: string) => {
    try {
      await remove(listingId);
      setSelectedListing(null);
      setCurrentPage("discover");
    } catch (caught) {
      setActionError(caught instanceof Error ? caught.message : "Could not delete listing");
    }
  };

  const handleChat = async (listing: Listing) => {
    if (!isAuthenticated) {
      setCurrentPage("auth");
      return;
    }
    try {
      const conversation = await api.startConversation(listing.id);
      setConversationId(conversation.id);
      setCurrentPage("chat");
    } catch (caught) {
      setActionError(caught instanceof Error ? caught.message : "Could not start conversation");
    }
  };

  const renderPage = () => {
    switch (currentPage) {
      case "resetPassword":
        if (!resetLink) return null;
        return <ResetPasswordPage lang={lang} link={resetLink} onDone={() => setCurrentPage("auth")} />;
      case "magicLink":
        if (!magicLink) return null;
        return <MagicLinkPage lang={lang} link={magicLink} onSignedIn={async () => {
          setMagicLink(null);
          setCurrentUser(mapUser(await api.me()));
          setCurrentPage("discover");
          await reload();
        }} />;
      case "verifyEmail":
        if (!verifyLink) return null;
        return <VerifyEmailPage lang={lang} link={verifyLink} onVerified={async user => {
          setVerifyLink(null);
          if (user) {
            setCurrentUser(user);
            setCurrentPage("discover");
            return;
          }
          try {
            setCurrentUser(mapUser(await api.me()));
            setCurrentPage("discover");
          } catch {
            setCurrentPage("auth");
          }
        }} />;
      case "auth":
        return <AuthPage lang={lang} onAuth={handleAuth} onEnterApp={() => setCurrentPage("discover")}
          error={authError} loading={authLoading} />;
      case "listing":
        if (!selectedListing) return null;
        return <ListingDetailPage listing={selectedListing} lang={lang} currentUser={currentUser}
          displayCurrency={currency} onBack={() => handleNav("discover")} onChat={handleChat}
          onViewProfile={id => { setViewUserId(id); setCurrentPage("profile"); }}
          onEditListing={listing => { setEditListing(listing); setShowCreateListing(true); }}
          onDeleteListing={id => void handleDeleteListing(id)}
          onSignIn={() => setCurrentPage("auth")} />;
      case "chat":
        return <ChatPage initialConversationId={conversationId} lang={lang} currentUser={currentUser} isAuthenticated={isAuthenticated}
          onSignIn={() => setCurrentPage("auth")} onLeaveReview={handleLeaveReview} />;
      case "profile":
        return <ProfilePage lang={lang} currentUser={currentUser} viewUserId={viewUserId}
          reviewContext={reviewContext} listings={listings} displayCurrency={currency}
          isAuthenticated={isAuthenticated} onSignIn={() => setCurrentPage("auth")}
          onSelectListing={listing => { setSelectedListing(listing); setCurrentPage("listing"); }}
          onViewAnalytics={() => setCurrentPage("analytics")}
          onReviewContextClear={() => setReviewContext(undefined)} />;
      case "settings":
        return <SettingsPage lang={lang} onLangChange={setLang} currency={currency} onCurrencyChange={setCurrency}
          theme={theme} onThemeChange={setTheme}
          currentUser={currentUser} isAuthenticated={isAuthenticated} onSignOut={handleSignOut} onSignIn={() => setCurrentPage("auth")}
          onAdmin={() => setCurrentPage("admin")} />;
      case "analytics":
        return <AnalyticsPage lang={lang} currentUser={currentUser} onBack={() => setCurrentPage("profile")} />;
      case "admin":
        return <AdminPage lang={lang} currentUser={currentUser} onBack={() => setCurrentPage("settings")} />;
      default:
        return <DiscoverPage lang={lang} listings={listings} loading={loading} error={error}
          displayCurrency={currency} onRetry={() => void reload()}
          onSelectListing={listing => { setSelectedListing(listing); setCurrentPage("listing"); }}
          onCreateListing={() => {
            if (!isAuthenticated) {
              setCurrentPage("auth");
              return;
            }
            if (!currentUser?.emailVerified) {
              setActionError(i18n[lang].verifyEmailBeforeListing);
              setCurrentPage("settings");
              return;
            }
            setShowCreateListing(true);
          }}
          isAuthenticated={isAuthenticated} />;
    }
  };

  const showNav = currentPage !== "auth" && currentPage !== "listing" && currentPage !== "resetPassword"
    && currentPage !== "magicLink" && currentPage !== "verifyEmail";
  return (
    <div className="relative flex flex-col md:flex-row bg-background min-h-dvh h-dvh w-full overflow-hidden">
      {actionError && <button onClick={() => setActionError("")} className="absolute top-2 left-3 right-3 md:left-auto md:right-4 md:max-w-md z-[80] p-2 text-xs btn-danger-outline">{actionError} · ✕</button>}
      {showNav && <Navigation current={currentPage} onNav={handleNav} isAuthenticated={isAuthenticated} lang={lang} unreadChats={0} />}
      <main className={`flex-1 overflow-hidden flex flex-col min-w-0 ${showNav ? "bottom-safe md:bottom-0 md:pl-56" : ""}`}>
        <div className="flex-1 min-h-0 overflow-hidden flex flex-col h-full">{renderPage()}</div>
      </main>
      {showCreateListing && <CreateListingModal lang={lang} onClose={() => { setShowCreateListing(false); setEditListing(undefined); }}
        onSubmit={(data, photoFile) => void handleCreateListing(data, photoFile)} editListing={editListing} sellerRole={currentUser?.role || "personal"} />}
    </div>
  );
}
