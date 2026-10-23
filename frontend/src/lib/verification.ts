/** Highest public trust badge to show (ID/passport beat email). */

export type VerificationTier = "none" | "email" | "id" | "passport";

export type SellerVerificationType = "" | "id" | "passport";

export interface VerificationSource {
  isEmailVerified: boolean;
  isVerifiedSeller: boolean;
  sellerVerificationType?: SellerVerificationType | null;
}

export function publicVerificationTier(source: VerificationSource): VerificationTier {
  if (source.isVerifiedSeller) {
    return source.sellerVerificationType === "passport" ? "passport" : "id";
  }
  if (source.isEmailVerified) return "email";
  return "none";
}

export function hasPublicVerificationBadge(tier: VerificationTier): boolean {
  return tier !== "none";
}

type VerificationCopy = {
  verified: string;
  notVerified: string;
  emailVerified: string;
  idCard: string;
  passport: string;
};

/** Single-line label for profile and listing seller rows. */
export function verificationBadgeLabel(tier: VerificationTier, t: VerificationCopy): string {
  switch (tier) {
    case "passport":
      return `✓ ${t.verified} (${t.passport})`;
    case "id":
      return `✓ ${t.verified} (${t.idCard})`;
    case "email":
      return `✓ ${t.emailVerified}`;
    default:
      return `○ ${t.notVerified}`;
  }
}
