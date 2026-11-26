import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ErrorBoundary } from "./ErrorBoundary";

function rendered(failed: boolean, language: string | null): string {
  vi.stubGlobal("localStorage", { getItem: () => language });
  const boundary = new ErrorBoundary({ children: <p>the app</p> });
  boundary.state = { failed };
  return renderToStaticMarkup(<>{boundary.render()}</>);
}

describe("ErrorBoundary", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("shows the app while nothing has crashed", () => {
    expect(rendered(false, "en")).toContain("the app");
  });

  it("switches to the fallback when a render error is caught", () => {
    expect(ErrorBoundary.getDerivedStateFromError()).toEqual({ failed: true });
  });

  it("replaces a crashed app with a reload screen in the user's language", () => {
    const english = rendered(true, "en");
    expect(english).not.toContain("the app");
    expect(english).toContain("Something went wrong");
    expect(english).toContain("Reload");
    expect(rendered(true, null)).toContain("เกิดข้อผิดพลาด");
  });
});
