export interface VerifyLink {
  uid: string;
  token: string;
}

/** Reads an email-verification link from the URL fragment (`#verify_uid=…&verify_token=…`). */
export function readVerifyLink(hash: string): VerifyLink | null {
  const params = new URLSearchParams(hash.replace(/^#/, ""));
  const uid = params.get("verify_uid");
  const token = params.get("verify_token");
  return uid && token ? { uid, token } : null;
}
