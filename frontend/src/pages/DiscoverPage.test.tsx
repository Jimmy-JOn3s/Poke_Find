import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { MOCK_LISTINGS } from "../mockData";
import DiscoverPage from "./DiscoverPage";


describe("discovery availability", () => {
  it.each(["reserved", "sold", "hidden", "draft", "completed"] as const)("excludes %s cards, including the seller's own listings", status => {
    const html = renderToStaticMarkup(
      <DiscoverPage lang="en" displayCurrency="THB" isAuthenticated
        listings={[
          { ...MOCK_LISTINGS[0], id: "available", productName: "Available card", status: "active" },
          { ...MOCK_LISTINGS[0], id: "unavailable", productName: "Unavailable card", status },
        ]}
        onSelectListing={() => {}} onCreateListing={() => {}} />,
    );
    expect(html).toContain("Available card");
    expect(html).not.toContain("Unavailable card");
  });
});
