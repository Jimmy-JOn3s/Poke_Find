import { describe, expect, it } from "vitest";
import { publicVerificationTier, verificationBadgeLabel } from "./verification";

const copy = {
  verified: "Verified",
  notVerified: "Not verified",
  emailVerified: "Email verified",
  idCard: "National ID",
  passport: "Passport",
};

describe("publicVerificationTier", () => {
  it("prefers passport over email", () => {
    expect(publicVerificationTier({
      isEmailVerified: true,
      isVerifiedSeller: true,
      sellerVerificationType: "passport",
    })).toBe("passport");
  });

  it("prefers id over email", () => {
    expect(publicVerificationTier({
      isEmailVerified: true,
      isVerifiedSeller: true,
      sellerVerificationType: "id",
    })).toBe("id");
  });

  it("shows email when seller is not identity-verified", () => {
    expect(publicVerificationTier({
      isEmailVerified: true,
      isVerifiedSeller: false,
      sellerVerificationType: "",
    })).toBe("email");
  });

  it("shows none when nothing is verified", () => {
    expect(publicVerificationTier({
      isEmailVerified: false,
      isVerifiedSeller: false,
    })).toBe("none");
  });
});

describe("verificationBadgeLabel", () => {
  it("uses email copy only for the email tier", () => {
    expect(verificationBadgeLabel("email", copy)).toBe("✓ Email verified");
    expect(verificationBadgeLabel("id", copy)).toBe("✓ Verified (National ID)");
  });
});
