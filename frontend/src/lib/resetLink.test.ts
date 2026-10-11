import { describe, expect, it } from "vitest";
import { readResetLink } from "./resetLink";

describe("readResetLink", () => {
  it("reads the uid and token from the URL fragment", () => {
    expect(readResetLink("#reset_uid=MQ&reset_token=c1x2y3-abc123")).toEqual({ uid: "MQ", token: "c1x2y3-abc123" });
  });

  it("ignores fragments without both parts", () => {
    expect(readResetLink("")).toBeNull();
    expect(readResetLink("#reset_uid=MQ")).toBeNull();
    expect(readResetLink("#reset_token=abc")).toBeNull();
    expect(readResetLink("#section-2")).toBeNull();
  });
});
