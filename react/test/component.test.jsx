import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render } from "@testing-library/react";
import QuranMadinaHtml, { loadQuranMadinaHtml } from "../src/index.js";

const tag = (container) => container.querySelector("quran-madina-html");

afterEach(() => {
  cleanup();
  document.querySelectorAll("script").forEach((s) => s.remove());
});

describe("<QuranMadinaHtml>", () => {
  it("exports the component and the loader", () => {
    expect(typeof QuranMadinaHtml).toBe("function");
    expect(typeof loadQuranMadinaHtml).toBe("function");
  });

  // Runs before any other rendering test so the module-level loader singleton is still fresh.
  it("injects the loader script once across multiple instances", () => {
    render(
      <div>
        <QuranMadinaHtml page={1} />
        <QuranMadinaHtml sura={2} aya={3} />
      </div>
    );
    expect(document.querySelectorAll('script[src*="quran-madina-html"]')).toHaveLength(1);
  });

  it("renders the custom element and sets the page attribute", () => {
    const { container } = render(<QuranMadinaHtml page={106} />);
    const el = tag(container);
    expect(el).toBeTruthy();
    expect(el.getAttribute("page")).toBe("106");
    expect(el.hasAttribute("sura")).toBe(false);
    expect(el.hasAttribute("aya")).toBe(false);
  });

  it("sets sura, aya and words for a range selection", () => {
    const { container } = render(<QuranMadinaHtml sura={2} aya="8-10" words="1:2" />);
    const el = tag(container);
    expect(el.getAttribute("sura")).toBe("2");
    expect(el.getAttribute("aya")).toBe("8-10");
    expect(el.getAttribute("words")).toBe("1:2");
    expect(el.hasAttribute("page")).toBe(false);
  });

  it("lets page win when both page and sura/aya are provided", () => {
    const { container } = render(<QuranMadinaHtml page={5} sura={2} aya="8-10" />);
    const el = tag(container);
    expect(el.getAttribute("page")).toBe("5");
    expect(el.hasAttribute("sura")).toBe(false);
    expect(el.hasAttribute("aya")).toBe(false);
  });

  it("treats headless as a boolean attribute, toggled on rerender", () => {
    const { container, rerender } = render(<QuranMadinaHtml sura={1} aya={1} headless />);
    const el = tag(container);
    expect(el.hasAttribute("headless")).toBe(true);
    expect(el.getAttribute("headless")).toBe("");

    rerender(<QuranMadinaHtml sura={1} aya={1} />);
    expect(el.hasAttribute("headless")).toBe(false);
  });

  it("treats notitle as a boolean attribute, toggled on rerender", () => {
    const { container, rerender } = render(
      <QuranMadinaHtml sura={1} aya={7} words="1-14" notitle />
    );
    const el = tag(container);
    expect(el.hasAttribute("notitle")).toBe(true);
    expect(el.getAttribute("notitle")).toBe("");

    rerender(<QuranMadinaHtml sura={1} aya={7} words="1-14" />);
    expect(el.hasAttribute("notitle")).toBe(false);
  });

  it("sets quotes and inline as plain string attributes, toggled on rerender", () => {
    const { container, rerender } = render(
      <QuranMadinaHtml sura={1} aya={1} quotes="no" inline="no" />
    );
    const el = tag(container);
    expect(el.getAttribute("quotes")).toBe("no");
    expect(el.getAttribute("inline")).toBe("no");

    rerender(<QuranMadinaHtml sura={1} aya={1} />);
    expect(el.hasAttribute("quotes")).toBe(false);
    expect(el.hasAttribute("inline")).toBe(false);
  });

  it("clears stale attributes when switching from page to sura/aya", () => {
    const { container, rerender } = render(<QuranMadinaHtml page={3} />);
    const el = tag(container);
    expect(el.getAttribute("page")).toBe("3");

    rerender(<QuranMadinaHtml sura={1} aya={2} />);
    expect(el.hasAttribute("page")).toBe(false);
    expect(el.getAttribute("sura")).toBe("1");
    expect(el.getAttribute("aya")).toBe("2");
  });

  it("passes className and style through to the element", () => {
    const { container } = render(
      <QuranMadinaHtml page={1} className="my-quran" style={{ color: "rgb(255, 0, 0)" }} />
    );
    const el = tag(container);
    expect(el.getAttribute("class")).toBe("my-quran");
    expect(el.style.color).toBe("rgb(255, 0, 0)");
  });
});
