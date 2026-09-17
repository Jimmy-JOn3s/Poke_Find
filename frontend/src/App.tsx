import { useEffect, useState } from "react";
import type { AppLang, Currency, Listing, Page, User, UserRole } from "./types";
import Navigation from "./components/Navigation";
import CreateListingModal from "./components/CreateListingModal";
import DiscoverPage from "./pages/DiscoverPage";
import AuthPage from "./pages/AuthPage";
import ListingDetailPage from "./pages/ListingDetailPage";
import ChatPage from "./pages/ChatPage";
import ProfilePage from "./pages/ProfilePage";
import SettingsPage from "./pages/SettingsPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import { api, mapListing, mapUser, setAccessToken } from "./lib/api";
import { useListings } from "./hooks/useListings";


function storedPreference<T extends string>(key: string, fallback: T): T {
  return (localStorage.getItem(key) as T | null) || fallback;
}


export default function App() {
  const [lang, setLangState] = useState<AppLang>(() => storedPreference("pokefind.language", "th"));
  const [currency, setCurrencyState] = useState<Currency>(() => storedPreference("pokefind.currency", "THB"));
  const [currentPage, setCurrentPage] = useState<Page>("discover");
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null);
  const [viewUserId, setViewUserId] = useState<string | undefined>();
  const [showCreateListing, setShowCreateListing] = useState(false);
  const [editListing, setEditListing] = useState<Listing | undefined>();
  const [authError, setAuthError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [actionError, setActionError] = useState("");
  const { listings, loading, error, reload, create, remove, setListings } = useListings();

  const isAuthenticated = Boolean(currentUser);

  useEffect(() => {
    api.me().then(user => {
      const mapped = mapUser(user);
      setCurrentUser(mapped);
      if (mapped.preferredLanguage) setLangState(mapped.preferredLanguage);
      if (mapped.preferredCurrency) setCurrencyState(mapped.preferredCurrency);
    }).catch(() => setAccessToken(null));
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

  const handleAuth = async (role: UserRole, name: string, email: string, password: string, mode: "signin" | "signup") => {
    setAuthLoading(true);
    setAuthError("");
    try {
      if (mode === "signup") {
        const usernameBase = email.split("@")[0].replace(/[^a-zA-Z0-9_-]/g, "-") || "trainer";
        const result = await api.register({
          username: `${usernameBase}-${Date.now().toString().slice(-5)}`, email, password,
          display_name: name, role, preferred_language: lang, preferred_currency: currency,
        });
        setAccessToken(result.access);
        setCurrentUser(mapUser(result.user));
      } else {
        const result = await api.login(email, password);
        setAccessToken(result.access);
        setCurrentUser(mapUser(await api.me()));
      }
      setCurrentPage("discover");
      await reload();
    } catch (caught) {
      setAuthError(caught instanceof Error ? caught.message : "Authentication failed");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleSignOut = () => {
    setAccessToken(null);
    setCurrentUser(null);
    setCurrentPage("discover");
    void reload();
  };

  const handleNav = (page: Page) => {
    setSelectedListing(null);
    setViewUserId(undefined);
    setCurrentPage(page);
  };

  const handleCreateListing = async (data: Partial<Listing>) => {
    setActionError("");
    const payload = {
      product_name: data.productName, set_name: data.set, set_code: data.setCode,
      card_number: data.cardNumber, condition: data.condition, card_language: data.language,
      rarity: data.rarity || "rare", asking_price: String(data.listedPrice), currency: data.currency || currency,
      quantity: data.quantity || 1, description: data.description || "", status: "active",
    };
    try {
      if (editListing) {
        const updated = mapListing(await api.updateListing(editListing.id, payload));
        setListings(current => current.map(item => item.id === updated.id ? updated : item));
      } else {
        await create(payload);
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
      await api.startConversation(listing.id);
      setCurrentPage("chat");
    } catch (caught) {
      setActionError(caught instanceof Error ? caught.message : "Could not start conversation");
    }
  };

  const renderPage = () => {
    switch (currentPage) {
      case "auth":
        return <AuthPage lang={lang} onAuth={handleAuth} error={authError} loading={authLoading} />;
      case "listing":
        if (!selectedListing) return null;
        return <ListingDetailPage listing={selectedListing} lang={lang} currentUser={currentUser}
          displayCurrency={currency} onBack={() => handleNav("discover")} onChat={handleChat}
          onViewProfile={id => { setViewUserId(id); setCurrentPage("profile"); }}
          onEditListing={listing => { setEditListing(listing); setShowCreateListing(true); }}
          onDeleteListing={id => void handleDeleteListing(id)} />;
      case "chat":
        return <ChatPage lang={lang} currentUser={currentUser} isAuthenticated={isAuthenticated} onSignIn={() => setCurrentPage("auth")} />;
      case "profile":
        return <ProfilePage lang={lang} currentUser={currentUser} viewUserId={viewUserId}
          listings={listings} displayCurrency={currency}
          isAuthenticated={isAuthenticated} onSignIn={() => setCurrentPage("auth")}
          onSelectListing={listing => { setSelectedListing(listing); setCurrentPage("listing"); }}
          onViewAnalytics={() => setCurrentPage("analytics")} />;
      case "settings":
        return <SettingsPage lang={lang} onLangChange={setLang} currency={currency} onCurrencyChange={setCurrency}
          currentUser={currentUser} isAuthenticated={isAuthenticated} onSignOut={handleSignOut} onSignIn={() => setCurrentPage("auth")} />;
      case "analytics":
        return <AnalyticsPage lang={lang} currentUser={currentUser} onBack={() => setCurrentPage("profile")} />;
      default:
        return <DiscoverPage lang={lang} listings={listings} loading={loading} error={error}
          displayCurrency={currency} onRetry={() => void reload()}
          onSelectListing={listing => { setSelectedListing(listing); setCurrentPage("listing"); }}
          onCreateListing={() => isAuthenticated ? setShowCreateListing(true) : setCurrentPage("auth")}
          isAuthenticated={isAuthenticated} />;
    }
  };

  const showNav = currentPage !== "auth" && currentPage !== "listing";
  return (
    <div className="relative flex flex-col md:flex-row bg-background min-h-dvh h-dvh w-full overflow-hidden">
      {actionError && <button onClick={() => setActionError("")} className="absolute top-2 left-3 right-3 md:left-auto md:right-4 md:max-w-md z-[80] p-2 text-xs"
        style={{ background: "#3a0b19", border: "1px solid #FF3D57", color: "#fff", borderRadius: 4 }}>{actionError} · ✕</button>}
      {showNav && <Navigation current={currentPage} onNav={handleNav} isAuthenticated={isAuthenticated} lang={lang} unreadChats={0} />}
      <main className={`flex-1 overflow-hidden flex flex-col min-w-0 ${showNav ? "bottom-safe md:bottom-0 md:pl-56" : ""}`}>
        <div className="flex-1 overflow-hidden flex flex-col h-full">{renderPage()}</div>
      </main>
      {showCreateListing && <CreateListingModal lang={lang} onClose={() => { setShowCreateListing(false); setEditListing(undefined); }}
        onSubmit={data => void handleCreateListing(data)} editListing={editListing} sellerRole={currentUser?.role || "personal"} />}
    </div>
  );
}
