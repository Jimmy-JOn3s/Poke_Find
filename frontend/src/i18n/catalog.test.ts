import { describe, expect, it } from "vitest";
import { i18n } from "../i18n";


describe("translation catalogue", () => {
  it("keeps Thai and English keys in parity", () => {
    expect(Object.keys(i18n.th).sort()).toEqual(Object.keys(i18n.en).sort());
  });

  it("contains the bilingual currency and network copy required by the MVP", () => {
    for (const locale of [i18n.th, i18n.en]) {
      expect(locale).toHaveProperty("displayCurrency");
      expect(locale).toHaveProperty("thaiBaht");
      expect(locale).toHaveProperty("usDollar");
      expect(locale).toHaveProperty("tryAgain");
    }
  });
});
