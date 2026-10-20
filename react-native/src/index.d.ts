import * as React from "react";
import type { StyleProp, ViewStyle } from "react-native";
import type { WebViewProps } from "react-native-webview";

export interface QuranMadinaNativeProps {
  /** A full page (1-604; IndoPak 1-610). Wins over sura/aya. */
  page?: number | string;
  /** Sura number (1-114), with `aya`. */
  sura?: number | string;
  /** Verse or range, e.g. 255 or "8-10". */
  aya?: number | string;
  /** Show only these words: "1:2", "3-10" or one number. */
  words?: string;
  /** Word range marked soft yellow, e.g. "5-8". */
  highlight?: string;
  /** Word range marked soft red; wins over highlight. */
  error?: string;
  /** Letters to emphasise: "word:letters colour blink" groups, e.g. "1:3, 4:3-5 emerald blink". */
  letters?: string;
  /** Only the Quran text, without the header (sura name, copy, translate). */
  headless?: boolean;
  /** With `words` crossing into a new sura: hide its name, keep the frame. */
  notitle?: boolean;
  /** "no" drops the quote marks around inline (single-line) renders. */
  quotes?: string;
  /** "no" forces the multiline layout. */
  inline?: string;
  /**
   * Which verse actions this tag offers when a verse is tapped: ids such as
   * `["copy", "bookmark"]` (or "copy bookmark"); `[]` or "none" for none (the verses are then
   * plain text, and the header icons go too). Default: all of them.
   */
  actions?: string[] | string;
  /** Your own verse actions, as buttons in the popup a tap on a verse opens. */
  ayaActions?: QuranAyaAction[];
  /** Called when one of `ayaActions` is chosen. */
  onAyaAction?: (selection: QuranAyaSelection) => void;
  /** Print: "1441H" (default), "1405H" or "IndoPak". */
  layout?: "1441H" | "1405H" | "IndoPak" | string;
  /** Font size in points (default 16). Any size works. */
  fontSize?: number;
  /** CSS colour of the text, e.g. "#ece6d6" on a dark screen. Mark colours adapt to it. */
  textColor?: string;
  /** CSS colour behind the text (default transparent). */
  backgroundColor?: string;
  /** Fixed height; by default the component takes the height of the text. */
  height?: number;
  /**
   * Load the library from the app (written by `npx quran-madina-native-bundle`): `true` for
   * the default folders, or the URL of another folder. Renders offline.
   */
  bundled?: boolean | string;
  /** Links the library opens (the translate buttons). Default: Linking.openURL. */
  onOpenUrl?: (url: string) => void;
  /** Library script URL (default: unpkg, latest 2.x). Ignored with `bundled`. */
  src?: string;
  /** Base URL of the library's files (default: unpkg). Ignored with `bundled`. */
  cdn?: string;
  /** Style of the outer View (the height is set by the component unless you set one). */
  style?: StyleProp<ViewStyle>;
  /** Extra props for the WebView. */
  webViewProps?: Partial<WebViewProps>;
}

/** A verse action: a button in the popup a tap on a verse opens. */
export interface QuranAyaAction {
  /** Unique id; "copy" and "translate" are the built-in ones. */
  id: string;
  /** Tooltip and accessible name. */
  title?: string;
  /** SVG markup (`currentColor` follows the popup) or an image URL. */
  icon?: string;
  /** Position in the popup: copy is 10, translate 20; default 100. */
  order?: number;
}

/** The verse an action was chosen on. */
export interface QuranAyaSelection {
  /** The action's id. */
  id: string;
  sura: number;
  aya: number;
  /** The Mushaf page of the verse in the current print. */
  page: number | null;
  /** The verse text. */
  text: string;
  suraName: string;
  layout: string;
}

declare const QuranMadinaNative: React.FC<QuranMadinaNativeProps>;
export default QuranMadinaNative;
export { QuranMadinaNative };

/** Folder name the bundle command writes ("quran-madina"). */
export declare const BUNDLE_FOLDER: string;
/** URL of the bundled folder on a platform. */
export declare function bundleBase(bundled: true | string, os?: string): string;
export declare const DEFAULT_SRC: string;
export declare const DEFAULT_CDN: string;
export declare function tagAttributes(props: Partial<QuranMadinaNativeProps>): Record<string, string>;
export declare function attributeUpdates(
  from: Record<string, string>,
  to: Record<string, string>
): Record<string, string | null>;
export declare function hostPage(config: Record<string, unknown> | null): string;
