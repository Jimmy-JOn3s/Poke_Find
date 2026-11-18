import { describe, expect, it } from "vitest";
import { canCreateListing, requiresPersonalIdVerification } from "./listingEligibility";
import type { User } from "../types";

const base: User = {
  id: "1",
  name: "Ash",
  email: "ash@example.com",
  avatar: "A",
  role: "personal",
  verified: false,
  emailVerified: true,
  verificationTier: "email",
  rating: 5,
  reviewCount: 0,
  totalSold: 0,
  joinedDate: "2026-01-01",
  location: "",
  bio: "",
};

describe("requiresPersonalIdVerification", () => {
  it("requires ID for personal sellers without staff approval", () => {
    expect(requiresPersonalIdVerification({ role: "personal", verified: false })).toBe(true);
    expect(requiresPersonalIdVerification({ role: "personal", verified: true })).toBe(false);
  });

  it("does not require ID for business accounts", () => {
    expect(requiresPersonalIdVerification({ role: "business", verified: false })).toBe(false);
  });
});

describe("canCreateListing", () => {
  it("blocks personal accounts with email only", () => {
    expect(canCreateListing(base)).toBe(false);
  });

  it("allows verified personal sellers", () => {
    expect(canCreateListing({ ...base, verified: true, verificationTier: "id" })).toBe(true);
  });

  it("allows business sellers with verified email only", () => {
    expect(canCreateListing({ ...base, role: "business" })).toBe(true);
  });
});