/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useInsertScriptTags } from 'keycloakify/tools/useInsertScriptTags';
import { useEffect } from 'react';

const THEME_STORAGE_KEY = '@i-am-bee/agentstack/THEME';
const THEME_URL_PARAM = 'kc_theme';
const VALID_THEMES = ['System', 'Dark', 'Light'] as const;
const DEFAULT_THEME = 'System' satisfies (typeof VALID_THEMES)[number];

/**
 * Injects theme script to apply the correct theme based on kc_theme URL parameter.
 * Supports Dark, Light, and System themes. Falls back to system preference if no parameter is provided.
 * This must run as early as possible in the page lifecycle to prevent theme flash.
 */
export function useApplyThemeScript() {
  const applyThemeScript = `
(() => {
  try {
    const html = document.documentElement;
    
    const urlParams = new URLSearchParams(window.location.search);
    const themeParam = urlParams.get('${THEME_URL_PARAM}');
    
    let themePreference = '${DEFAULT_THEME}';
    const validThemes = ${JSON.stringify(VALID_THEMES)};

    if (themeParam && validThemes.includes(themeParam)) {
      themePreference = themeParam;
      try {
        window.localStorage.setItem('${THEME_STORAGE_KEY}', JSON.stringify(themeParam));
      } catch (e) {
        console.warn('Failed to save theme preference to localStorage', e);
      }
    } else {
      try {
        const stored = window.localStorage.getItem('${THEME_STORAGE_KEY}');
        if (stored) {
          const parsedTheme = JSON.parse(stored);
          if (validThemes.includes(parsedTheme)) {
            themePreference = parsedTheme;
          }
        }
      } catch (e) {
        console.warn('Failed to load theme preference from localStorage', e);
      }
    }
    
    let isDarkMode = themePreference === 'Dark';
    if (themePreference === 'System') {
      isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    }

    if (isDarkMode) {
      html.classList.add('cds--g90');
      html.classList.remove('cds--white');
    } else {
      html.classList.add('cds--white');
      html.classList.remove('cds--g90');
    }
  } catch (error) {
    console.warn('Failed to apply theme', error); 
  }
})();
`;

  const { insertScriptTags } = useInsertScriptTags({
    componentOrHookName: 'ApplyThemeScript',
    scriptTags: [
      {
        type: 'text/javascript',
        textContent: applyThemeScript,
      },
    ],
  });

  useEffect(() => {
    insertScriptTags();
  }, [insertScriptTags]);
}
