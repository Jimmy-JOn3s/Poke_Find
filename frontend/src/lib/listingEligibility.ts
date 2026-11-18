import type { User } from "../types";

/** Personal sellers must be staff-approved on national ID or passport before listing. */
export function requiresPersonalIdVerification(user: Pick<User, "role" | "verified">): boolean {
  return user.role === "personal" && !user.verified;
}

export function canCreateListing(
  user: Pick<User, "role" | "verified" | "emailVerified">,
): boolean {
  if (requiresPersonalIdVerification(user)) return false;
  return user.emailVerified || user.verified;
}