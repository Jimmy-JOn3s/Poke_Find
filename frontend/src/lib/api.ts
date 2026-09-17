import type { CardCondition, CardLanguage, CardRarity, Currency, Listing, UserRole } from "../types";


const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
const TOKEN_KEY = "pokefind.accessToken";

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
export interface ApiDeal { id: number; status: "accepted" | "completed" | "cancelled"; final_price: string; currency: Currency; buyer_confirmed: boolean; seller_confirmed: boolean }
export interface ApiConversation {
  id: number;
  listing: { id: number; product_name: string; asking_price: string; currency: Currency };
  buyer: ApiUser;
  seller: ApiUser;
  latest_message: ApiMessage | null;
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

function accessToken(): string | null {
  return typeof localStorage === "undefined" ? null : localStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token: string | null): void {
  if (typeof localStorage === "undefined") return;
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const token = accessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
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
};
