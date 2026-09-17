import { describe, expect, it } from "vitest";
import { buildListingQuery, mapListing } from "./api";


describe("listing API adapter", () => {
  it("maps the backend contract into the existing generated UI model", () => {
    const listing = mapListing({
      id: 7,
      seller: { id: 2, display_name: "Poke BKK", role: "business", is_verified_seller: true },
      product_name: "Mew ex",
      set_name: "151",
      set_code: "SV2A",
      card_number: "205/165",
      condition: "NM",
      card_language: "th",
      rarity: "secret",
      asking_price: "2100.00",
      currency: "THB",
      quantity: 1,
      description: "Thai print",
      image_url: "https://assets.tcgdex.net/ja/SV/SV2a/205/high.webp",
      status: "active",
      created_at: "2026-09-13T10:00:00Z",
      is_saved: false,
      photo: null,
    });
    expect(listing.productName).toBe("Mew ex");
    expect(listing.imageUrl).toContain("tcgdex.net");
    expect(listing.sellerRole).toBe("business");
    expect(listing.currency).toBe("THB");
    expect(listing.listedPrice).toBe(2100);
  });

  it("omits empty filters and keeps supported search filters", () => {
    expect(buildListingQuery({ q: "mew", condition: "", currency: "USD" })).toBe("?q=mew&currency=USD");
  });
});
