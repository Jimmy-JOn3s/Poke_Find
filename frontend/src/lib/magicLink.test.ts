import { describe, expect, it } from "vitest";
import { readMagicLink } from "./magicLink";

describe("readMagicLink", () => {
  it("reads uid and token from the hash", () => {
    expect(readMagicLink("#magic_uid=abc&magic_token=xyz")).toEqual({ uid: "abc", token: "xyz" });
  });

  it("returns null when the hash is incomplete", () => {
    expect(readMagicLink("#magic_uid=abc")).toBeNull();
    expect(readMagicLink("")).toBeNull();
  });
});
