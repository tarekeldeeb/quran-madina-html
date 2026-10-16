import * as React from "react";

export interface QuranMadinaHtmlLoaderOptions {
  /** URL of the library script (default: https://unpkg.com/quran-madina-html). */
  src?: string;
  /** Base URL for the CSS + JSON assets (default: https://unpkg.com/quran-madina-html/). */
  cdn?: string;
  /**
   * data-layout: "1441H" (default) | "1405H" | "IndoPak". Letters are stretched like the
   * print and any font size works with one DB per layout.
   */
  layout?: "1441H" | "1405H" | "IndoPak" | string;
  /** @deprecated Ignored since 2.0 (every tag uses the v2 fonts; a warning is logged). */
  font?: string;
  /** @deprecated Ignored since 2.0 (a warning is logged). */
  name?: string;
  /** data-font-size in px (default 16). Any size works. */
  fontSize?: number | string;
}

export interface QuranMadinaHtmlProps
  extends QuranMadinaHtmlLoaderOptions,
    React.HTMLAttributes<HTMLElement> {
  /** Render a full page (1-604; IndoPak 1-610). Mutually exclusive with sura/aya. */
  page?: number | string;
  /** Sura number (1-114). Use together with `aya`. */
  sura?: number | string;
  /** Aya number or range, e.g. "8-10". Use together with `sura`. */
  aya?: number | string;
  /** Restrict to a 1-based word range, e.g. "1:2", "3-10", or a single index. */
  words?: string;
  /** 1-based inclusive word range (same syntax as `words`) to mark soft yellow. */
  highlight?: string;
  /**
   * 1-based inclusive word range (same syntax as `words`) marking a sub-range that should
   * render with the library's built-in "error" highlight styling.
   */
  error?: string;
  /** Drop the header / copy chrome and render only the Quran text. */
  headless?: boolean;
  /**
   * When a `words` selection crosses into a new sura, hide its name text while keeping the
   * decorated title line (the ornamental frame stays, empty); the basmala, being real counted
   * words, still renders. Ignored by page/aya renders.
   */
  notitle?: boolean;
  /** Set to "no" (or "false") to drop the quote marks shown around inline (single-line) renders. */
  quotes?: "no" | "auto" | "yes" | boolean | string;
  /**
   * "no": force the multiline/header layout even if the selection would fit one line.
   * "auto" (default): fit-based layout, same as omitting the prop.
   * "yes": force a single inline line even if the selection overflows it - not implemented yet,
   * falls back to "auto" with a console warning from the underlying library.
   */
  inline?: "no" | "auto" | "yes" | string;
}

/** Inject the loader script once; resolves when the custom element is registered. */
export function loadQuranMadinaHtml(
  opts?: QuranMadinaHtmlLoaderOptions
): Promise<void>;

declare const QuranMadinaHtml: React.FC<QuranMadinaHtmlProps>;
export default QuranMadinaHtml;
