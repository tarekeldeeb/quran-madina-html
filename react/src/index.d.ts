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
  /**
   * Load the app's own copy of the library instead of unpkg, for offline use. Write it with
   * `npx quran-madina-bundle` (default: public/quran-madina). `true` loads it from
   * "/quran-madina/"; a string is the URL the bundle folder is served at. Overrides src and cdn.
   */
  bundled?: boolean | string;
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
  /**
   * Letters to emphasise inside words: comma-separated groups "word:letters [colour] [blink]",
   * e.g. "1:3 crimson, 4:3-5 emerald blink, 6:2+4". Word numbers count like highlight/error;
   * letters are n, n-m or n+m; the colour is optional (crimson by default): crimson, emerald,
   * lapis, gold, violet or any CSS colour; "blink" makes the letter's halo pulse (no animation
   * by default). Nothing moves.
   */
  letters?: string;
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
  /**
   * Which verse actions this tag offers on a click: ids such as `["copy", "bookmark"]` (or
   * "copy bookmark"); `[]` or "none" for none (the verses are then plain text, and the header
   * icons go too). Default: every registered action.
   */
  actions?: string[] | string;
}

/** The verse an action is offered on or chosen for. */
export interface QuranAya {
  sura: number;
  aya: number;
  /** The Mushaf page of the verse in the current print. */
  page: number | null;
  /** The verse text (computed when read). */
  readonly text: string;
  suraName: string;
  /** "1441H", "1405H" or "IndoPak". */
  layout: string;
  /** The <quran-madina-html> element. */
  tag: HTMLElement;
  /** The clicked line piece of the verse. */
  element: HTMLElement;
  /** Close the popup (it also closes after any action). */
  close(): void;
}

/** A verse action: a button in the popup a click on a verse opens. */
export interface QuranAyaAction {
  /** Unique id; registering the same id again replaces it. "copy" and "translate" are built in. */
  id: string;
  /** Tooltip and accessible name (default: the id). */
  title?: string;
  /** SVG markup (`currentColor` follows the popup), an image URL, or an element. */
  icon?: string | Element | (() => Element);
  /** Position in the popup: copy is 10, translate 20; default 100. */
  order?: number;
  /** Offer the action only on the verses this returns true for. */
  when?: (aya: QuranAya) => boolean;
  /** Runs when the button is clicked. */
  onSelect: (aya: QuranAya) => void;
}

/** Add an action (or replace the one with the same id), once the library is loaded. */
export declare function registerAction(spec: QuranAyaAction): Promise<string>;
/** Remove an action by id; resolves to whether it was there. */
export declare function unregisterAction(id: string): Promise<boolean>;
/** Remove every action, the built-ins too: verses become plain text. */
export declare function clearActions(): Promise<void>;
/** Back to the built-in copy and translate. */
export declare function resetActions(): Promise<void>;
/** Register an action while the calling component is mounted. */
export declare function useAyaAction(spec: QuranAyaAction): void;

/** Inject the loader script once; resolves when the custom element is registered. */
export function loadQuranMadinaHtml(
  opts?: QuranMadinaHtmlLoaderOptions
): Promise<void>;

declare const QuranMadinaHtml: React.FC<QuranMadinaHtmlProps>;
export default QuranMadinaHtml;

/** URL the default bundle folder (public/quran-madina) is served at: "/quran-madina/". */
export declare const BUNDLE_BASE: string;

/** The script URL and asset base for a bundled copy of the library (see `bundled`). */
export declare function bundleUrls(bundled: true | string): { src: string; cdn: string };
