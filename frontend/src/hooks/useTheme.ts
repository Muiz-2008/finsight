import { useCallback, useEffect, useState } from "react";

export type Theme = "light" | "dark" | "system";

const STORAGE_KEY = "finsight_theme";

function readStoredTheme(): Theme {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark" || stored === "system") return stored;
  } catch {
    // localStorage can throw (private browsing, blocked storage) — fall
    // through to the default rather than crash the whole app over a
    // cosmetic preference.
  }
  return "system";
}

function applyTheme(theme: Theme) {
  // "system" means no attribute at all — the prefers-color-scheme media
  // query in index.css takes over. "light"/"dark" set it explicitly,
  // which the CSS's :root[data-theme=...] blocks key off of.
  if (theme === "system") {
    document.documentElement.removeAttribute("data-theme");
  } else {
    document.documentElement.setAttribute("data-theme", theme);
  }
}

/** Manual light/dark/system theme choice, persisted in localStorage.
 * Applied via a `data-theme` attribute on <html> that index.css reads —
 * see the CSS file for why "system" is the *absence* of that attribute
 * rather than a third value.
 */
export function useTheme(): { theme: Theme; setTheme: (t: Theme) => void } {
  const [theme, setThemeState] = useState<Theme>(readStoredTheme);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const setTheme = useCallback((t: Theme) => {
    setThemeState(t);
    try {
      localStorage.setItem(STORAGE_KEY, t);
    } catch {
      // Same reasoning as readStoredTheme: a failed write here just means
      // the choice won't survive a reload, not a broken app.
    }
  }, []);

  return { theme, setTheme };
}
