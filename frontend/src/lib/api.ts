import type { CardCondition, CardLanguage, CardRarity, Currency, Listing, Review, UserRole } from "../types";


const ACCESS_TOKEN_KEY = "pokefind.accessToken";
const REFRESH_TOKEN_KEY = "pokefind.refreshToken";

export function resolveApiBase(configured: string | undefined): string {
  const value = configured?.trim();
  if (!value) {
    throw new Error("VITE_API_URL is not set. Copy frontend/.env.example to frontend/.env.development.local.");
  }
  return value.replace(/\/+$/, "");
}

function apiBase(): string {
  return resolveApiBase(import.meta.env.VITE_API_URL);
}

export interface ApiUser {
  id: number;
  username?: string;
  email?: string;
  display_name: string;
  role: UserRole;
  is_verified_seller: boolean;
  preferred_language?: "th" | "en";
  preferred_currency?: Currency;
  avatar?: string | null;
  location?: string;
  bio?: string;
}

export interface ApiListing {
  id: number;
  seller: ApiUser;
  product_name: string;
  set_name: string;
  set_code: string;
  card_number: string;
  condition: CardCondition;
  card_language: CardLanguage;
  rarity: CardRarity;
  asking_price: string;
  currency: Currency;
  quantity: number;
  description: string;
  image_url: string;
  photo: string | null;
  status: string;
  is_saved: boolean;
  created_at: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: ApiUser;
}

export interface ApiMessage { id: number; author: ApiUser; body: string; created_at: string }
export interface ApiOffer { id: number; proposer: ApiUser; amount: string; currency: Currency; status: "pending" | "accepted" | "declined" | "countered"; created_at: string }
export interface ApiDeal {
  id: number;
  status: "accepted" | "completed" | "cancelled";
  final_price: string;
  currency: Currency;
  buyer_confirmed: boolean;
  seller_confirmed: boolean;
  reviewer_has_reviewed: boolean;
  counterparty_id: number | null;
  counterparty_name: string | null;
}

export interface ApiPublicProfile {
  id: number;
  display_name: string;
  role: UserRole;
  avatar?: string | null;
  location?: string;
  bio?: string;
  is_verified_seller: boolean;
  date_joined: string;
  rating: number;
  review_count: number;
  total_sold: number;
  pending_review_deal_id: number | null;
}

export interface ApiReview {
  id: number;
  deal: number;
  reviewer: ApiUser;
  reviewee: ApiUser;
  rating: number;
  comment: string;
  listing_name: string;
  created_at: string;
}
export interface ApiConversation {
  id: number;
  listing: { id: number; product_name: string; asking_price: string; currency: Currency };
  buyer: ApiUser;
  seller: ApiUser;
  latest_message: ApiMessage | null;
  unread_count: number;
  deal: ApiDeal | null;
  updated_at: string;
}

export type ListingFilters = Partial<Record<"q" | "condition" | "card_language" | "rarity" | "currency" | "min_price" | "max_price", string>>;

export function buildListingQuery(filters: ListingFilters): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function mapListing(item: ApiListing): Listing {
  const palettes = [
    ["#FF4500", "#FF8C00", "🔥"],
    ["#FFD700", "#FFA500", "⚡"],
    ["#9B59B6", "#E91E8C", "✨"],
    ["#06B6D4", "#0EA5E9", "🐉"],
  ];
  const palette = palettes[item.id % palettes.length];
  return {
    id: String(item.id), sellerId: String(item.seller.id), sellerName: item.seller.display_name,
    sellerAvatar: item.seller.display_name.slice(0, 1), sellerRole: item.seller.role,
    sellerVerified: item.seller.is_verified_seller, sellerRating: 5,
    productName: item.product_name, set: item.set_name, setCode: item.set_code,
    cardNumber: item.card_number, condition: item.condition, language: item.card_language,
    rarity: item.rarity, listedPrice: Number(item.asking_price), currency: item.currency,
    quantity: item.quantity, status: item.status as Listing["status"],
    gradientFrom: palette[0], gradientTo: palette[1], typeIcon: palette[2],
    createdAt: item.created_at.slice(0, 10), views: 0, likes: 0,
    description: item.description, imageUrl: item.image_url || undefined,
    photo: item.photo || undefined, isSaved: item.is_saved,
  };
}

export function mapUser(item: ApiUser) {
  return {
    id: String(item.id), name: item.display_name, email: item.email || "", avatar: item.display_name.slice(0, 1),
    role: item.role, verified: item.is_verified_seller, rating: 5, reviewCount: 0, totalSold: 0,
    joinedDate: new Date().toISOString().slice(0, 10), location: item.location || "", bio: item.bio || "",
    preferredLanguage: item.preferred_language, preferredCurrency: item.preferred_currency,
  };
}

export function mapPublicProfile(item: ApiPublicProfile) {
  return {
    id: String(item.id), name: item.display_name, email: "", avatar: item.display_name.slice(0, 1),
    role: item.role, verified: item.is_verified_seller, rating: item.rating, reviewCount: item.review_count,
    totalSold: item.total_sold, joinedDate: item.date_joined.slice(0, 10), location: item.location || "",
    bio: item.bio || "",
  };
}

export function mapReview(item: ApiReview): Review {
  return {
    id: String(item.id), reviewerId: String(item.reviewer.id), reviewerName: item.reviewer.display_name,
    reviewerAvatar: item.reviewer.display_name.slice(0, 1), reviewerRole: item.reviewer.role,
    rating: item.rating, comment: item.comment, date: item.created_at.slice(0, 10), listingName: item.listing_name,
  };
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

function readStorage(key: string): string | null {
  return typeof localStorage === "undefined" ? null : localStorage.getItem(key);
}

export function setTokens(tokens: AuthTokens | null): void {
  if (typeof localStorage === "undefined") return;
  if (tokens) {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
  } else {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
}

// One refresh at a time per tab: the server rotates refresh tokens, so a second concurrent
// refresh would present an already-blacklisted token and sign the user out.
let refreshInFlight: Promise<boolean> | null = null;

function refreshTokens(): Promise<boolean> {
  if (!refreshInFlight) {
    refreshInFlight = runRefresh().finally(() => { refreshInFlight = null; });
  }
  return refreshInFlight;
}

async function runRefresh(): Promise<boolean> {
  const refresh = readStorage(REFRESH_TOKEN_KEY);
  if (!refresh) {
    setTokens(null);
    return false;
  }
  const response = await fetch(`${apiBase()}/auth/refresh/`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh }),
  });
  if (response.ok) {
    const data = await response.json() as { access: string; refresh?: string };
    setTokens({ access: data.access, refresh: data.refresh ?? refresh });
    return true;
  }
  // Another tab may have rotated the refresh token while this request was in flight.
  if (readStorage(REFRESH_TOKEN_KEY) !== refresh) return true;
  // Only an explicit rejection ends the session; rate limits and server errors are retried later.
  if (response.status === 400 || response.status === 401) setTokens(null);
  return false;
}

function send(path: string, init: RequestInit, token: string | null): Promise<Response> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return fetch(`${apiBase()}${path}`, { ...init, headers });
}

// Credential endpoints never carry a session: a stale token would otherwise turn a wrong password
// (401) into a refresh plus a second login attempt, doubling the attempts the rate limit counts.
const CREDENTIAL_PATHS = new Set([
  "/auth/login/", "/auth/register/", "/auth/password-reset/", "/auth/password-reset/confirm/",
]);

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = CREDENTIAL_PATHS.has(path) ? null : readStorage(ACCESS_TOKEN_KEY);
  let response = await send(path, init, token);
  if (response.status === 401 && token) {
    const latest = readStorage(ACCESS_TOKEN_KEY);
    const refreshed = latest && latest !== token ? true : await refreshTokens();
    // Without a session, retry anonymously so public pages keep working.
    response = await send(path, init, refreshed ? readStorage(ACCESS_TOKEN_KEY) : null);
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || Object.values(payload).flat().join(" ") || `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  async listListings(filters: ListingFilters = {}): Promise<Listing[]> {
    const result = await request<{ results: ApiListing[] }>(`/listings/${buildListingQuery(filters)}`);
    return result.results.map(mapListing);
  },
  register(payload: Record<string, unknown>): Promise<AuthResponse> {
    return request("/auth/register/", { method: "POST", body: JSON.stringify(payload) });
  },
  login(username: string, password: string): Promise<{ access: string; refresh: string }> {
    return request("/auth/login/", { method: "POST", body: JSON.stringify({ username, password }) });
  },
  async logout(): Promise<void> {
    const refresh = readStorage(REFRESH_TOKEN_KEY);
    setTokens(null);
    if (!refresh) return;
    // Best effort: the user is signed out locally even if the network call fails.
    await fetch(`${apiBase()}/auth/logout/`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh }),
    }).catch(() => undefined);
  },
  requestPasswordReset(email: string): Promise<{ detail: string }> {
    return request("/auth/password-reset/", { method: "POST", body: JSON.stringify({ email }) });
  },
  confirmPasswordReset(uid: string, token: string, newPassword: string): Promise<{ detail: string }> {
    return request("/auth/password-reset/confirm/", {
      method: "POST", body: JSON.stringify({ uid, token, new_password: newPassword }),
    });
  },
  me(): Promise<ApiUser> { return request("/auth/me/"); },
  updateMe(payload: Partial<ApiUser>): Promise<ApiUser> {
    return request("/auth/me/", { method: "PATCH", body: JSON.stringify(payload) });
  },
  createListing(payload: Record<string, unknown>): Promise<ApiListing> {
    return request("/listings/", { method: "POST", body: JSON.stringify(payload) });
  },
  updateListing(id: string, payload: Record<string, unknown>): Promise<ApiListing> {
    return request(`/listings/${id}/`, { method: "PATCH", body: JSON.stringify(payload) });
  },
  deleteListing(id: string): Promise<void> {
    return request(`/listings/${id}/`, { method: "DELETE" });
  },
  saveListing(id: string, saved: boolean): Promise<{ saved: boolean }> {
    return request(`/listings/${id}/save/`, { method: saved ? "POST" : "DELETE" });
  },
  async conversations(): Promise<ApiConversation[]> {
    const result = await request<{ results: ApiConversation[] }>("/conversations/");
    return result.results;
  },
  startConversation(listingId: string): Promise<ApiConversation> {
    return request("/conversations/", { method: "POST", body: JSON.stringify({ listing_id: listingId }) });
  },
  messages(id: number): Promise<ApiMessage[]> { return request(`/conversations/${id}/messages/`); },
  markConversationRead(id: number, messageId: number): Promise<ApiConversation> {
    return request(`/conversations/${id}/read/`, { method: "POST", body: JSON.stringify({ message_id: messageId }) });
  },
  offers(id: number): Promise<ApiOffer[]> { return request(`/conversations/${id}/offers/`); },
  sendMessage(id: number, body: string): Promise<ApiMessage> {
    return request(`/conversations/${id}/messages/`, { method: "POST", body: JSON.stringify({ body }) });
  },
  createOffer(id: number, amount: string, currency: Currency): Promise<ApiOffer> {
    return request(`/conversations/${id}/offers/`, { method: "POST", body: JSON.stringify({ amount, currency }) });
  },
  acceptOffer(id: number): Promise<ApiOffer> { return request(`/offers/${id}/accept/`, { method: "POST" }); },
  declineOffer(id: number): Promise<ApiOffer> { return request(`/offers/${id}/decline/`, { method: "POST" }); },
  counterOffer(id: number, amount: string): Promise<ApiOffer> {
    return request(`/offers/${id}/counter/`, { method: "POST", body: JSON.stringify({ amount }) });
  },
  confirmDeal(id: number): Promise<ApiDeal> { return request(`/deals/${id}/confirm-completion/`, { method: "POST" }); },
  cancelDeal(id: number): Promise<ApiDeal> { return request(`/deals/${id}/cancel/`, { method: "POST" }); },
  submitReview(dealId: number, rating: number, comment: string): Promise<ApiReview> {
    return request(`/deals/${dealId}/review/`, { method: "POST", body: JSON.stringify({ rating, comment }) });
  },
  async userProfile(userId: string): Promise<ApiPublicProfile> {
    return request(`/auth/users/${userId}/`);
  },
  async userReviews(userId: string): Promise<Review[]> {
    const result = await request<{ results: ApiReview[] }>(`/auth/users/${userId}/reviews/`);
    return result.results.map(mapReview);
  },
};
