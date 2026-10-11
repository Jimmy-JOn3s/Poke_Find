export interface ResetLink {
  uid: string;
  token: string;
}

/** Reads a password-reset link from the URL fragment (`#reset_uid=…&reset_token=…`). */
export function readResetLink(hash: string): ResetLink | null {
  const params = new URLSearchParams(hash.replace(/^#/, ""));
  const uid = params.get("reset_uid");
  const token = params.get("reset_token");
  return uid && token ? { uid, token } : null;
}
