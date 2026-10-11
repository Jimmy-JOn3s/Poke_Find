import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api, resolveApiBase, setTokens } from "./api";

const API = "http://api.test/api";
const ME = { id: 1, display_name: "Ash", role: "personal", is_verified_seller: false };

function memoryStorage(): Storage {
  const data = new Map<string, string>();
  return {
    get length() { return data.size; },
    clear: () => data.clear(),
    getItem: (key: string) => data.get(key) ?? null,
    key: (index: number) => Array.from(data.keys())[index] ?? null,
    removeItem: (key: string) => { data.delete(key); },
    setItem: (key: string, value: string) => { data.set(key, String(value)); },
  };
}

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function bearer(init?: RequestInit): string | null {
  return new Headers(init?.headers).get("Authorization");
}

describe("API base URL", () => {
  it("requires VITE_API_URL instead of falling back to localhost", () => {
    expect(() => resolveApiBase(undefined)).toThrow(/VITE_API_URL/);
    expect(() => resolveApiBase("  ")).toThrow(/VITE_API_URL/);
    expect(resolveApiBase("https://api.example.com/api/")).toBe("https://api.example.com/api");
  });
});

describe("session tokens", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_API_URL", API);
    vi.stubGlobal("localStorage", memoryStorage());
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("refreshes an expired access token and retries the request", async () => {
    setTokens({ access: "old-access", refresh: "refresh-1" });
    vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
      if (url === `${API}/auth/refresh/`) return json(200, { access: "new-access", refresh: "refresh-2" });
      return bearer(init) === "Bearer new-access" ? json(200, ME) : json(401, { detail: "Token expired" });
    }));

    await expect(api.me()).resolves.toMatchObject({ display_name: "Ash" });
    expect(localStorage.getItem("pokefind.accessToken")).toBe("new-access");
    expect(localStorage.getItem("pokefind.refreshToken")).toBe("refresh-2");
  });

  it("shares one refresh between concurrent requests", async () => {
    setTokens({ access: "old-access", refresh: "refresh-1" });
    let refreshCalls = 0;
    vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
      if (url === `${API}/auth/refresh/`) {
        refreshCalls += 1;
        return json(200, { access: "new-access", refresh: "refresh-2" });
      }
      return bearer(init) === "Bearer new-access" ? json(200, ME) : json(401, { detail: "Token expired" });
    }));

    await Promise.all([api.me(), api.me(), api.me()]);
    expect(refreshCalls).toBe(1);
  });

  it("uses a token another tab already refreshed instead of refreshing again", async () => {
    setTokens({ access: "old-access", refresh: "refresh-1" });
    let refreshCalls = 0;
    vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
      if (url === `${API}/auth/refresh/`) {
        refreshCalls += 1;
        return json(401, { detail: "Token is blacklisted" });
      }
      if (bearer(init) === "Bearer old-access") {
        setTokens({ access: "other-tab-access", refresh: "refresh-2" });
        return json(401, { detail: "Token expired" });
      }
      return json(200, ME);
    }));

    await expect(api.me()).resolves.toMatchObject({ display_name: "Ash" });
    expect(refreshCalls).toBe(0);
  });

  it("clears tokens and retries anonymously when the refresh token is rejected", async () => {
    setTokens({ access: "old-access", refresh: "revoked" });
    vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
      if (url === `${API}/auth/refresh/`) return json(401, { detail: "Token is blacklisted" });
      return bearer(init) ? json(401, { detail: "Token expired" }) : json(200, { results: [] });
    }));

    await expect(api.listListings()).resolves.toEqual([]);
    expect(localStorage.getItem("pokefind.accessToken")).toBeNull();
    expect(localStorage.getItem("pokefind.refreshToken")).toBeNull();
  });

  it("keeps the session when refresh is only rate limited", async () => {
    setTokens({ access: "old-access", refresh: "refresh-1" });
    vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
      if (url === `${API}/auth/refresh/`) return json(429, { detail: "Slow down" });
      return bearer(init) ? json(401, { detail: "Token expired" }) : json(200, { results: [] });
    }));

    await api.listListings();
    expect(localStorage.getItem("pokefind.refreshToken")).toBe("refresh-1");
  });

  it("a failed login never sends a stored token or triggers a refresh", async () => {
    setTokens({ access: "stale-access", refresh: "refresh-1" });
    const fetchMock = vi.fn(async (_url: string, _init?: RequestInit) => json(401, { detail: "No active account" }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(api.login("ash@example.com", "wrong")).rejects.toThrow("No active account");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(bearer(fetchMock.mock.calls[0][1])).toBeNull();
  });

  it("password-reset calls never send a stored token", async () => {
    setTokens({ access: "stale-access", refresh: "refresh-1" });
    const fetchMock = vi.fn(async (_url: string, _init?: RequestInit) => json(200, { detail: "ok" }));
    vi.stubGlobal("fetch", fetchMock);

    await api.requestPasswordReset("ash@example.com");
    await api.confirmPasswordReset("MQ", "token-1", "brand-new-pass-92");
    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      `${API}/auth/password-reset/`, `${API}/auth/password-reset/confirm/`,
    ]);
    expect(fetchMock.mock.calls.map(([, init]) => bearer(init))).toEqual([null, null]);
    expect(JSON.parse(String(fetchMock.mock.calls[1][1]?.body))).toEqual({
      uid: "MQ", token: "token-1", new_password: "brand-new-pass-92",
    });
  });

  it("logout clears tokens and asks the server to blacklist the refresh token", async () => {
    setTokens({ access: "a", refresh: "r" });
    const fetchMock = vi.fn(async () => json(200, {}));
    vi.stubGlobal("fetch", fetchMock);

    await api.logout();
    expect(localStorage.getItem("pokefind.accessToken")).toBeNull();
    expect(fetchMock).toHaveBeenCalledWith(
      `${API}/auth/logout/`, expect.objectContaining({ body: JSON.stringify({ refresh: "r" }) }),
    );
  });
});
