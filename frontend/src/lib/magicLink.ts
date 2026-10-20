export interface MagicLink {
  uid: string;
  token: string;
}

/** Reads a magic-link sign-in URL from the fragment (`#magic_uid=…&magic_token=…`). */
export function readMagicLink(hash: string): MagicLink | null {
  const params = new URLSearchParams(hash.replace(/^#/, ""));
  const uid = params.get("magic_uid");
  const token = params.get("magic_token");
  return uid && token ? { uid, token } : null;
}
