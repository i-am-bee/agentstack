/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useInsertScriptTags } from 'keycloakify/tools/useInsertScriptTags';
import { useEffect } from 'react';

/**
 * Injects theme script to apply the correct theme based on kc_theme URL parameter.
 * Supports Dark, Light, and System themes. Falls back to system preference if no parameter is provided.
 * This must run as early as possible in the page lifecycle to prevent theme flash.
 */
export function useApplyThemeScript() {
  const darkModeScript = `
(() => {
  try {
    const html = document.documentElement;
    const THEME_STORAGE_KEY = '@i-am-bee/agentstack/THEME';
    
    const urlParams = new URLSearchParams(window.location.search);
    const themeParam = urlParams.get('kc_theme');
    
    let themePreference = 'System';
    
    if (themeParam) {
      themePreference = themeParam;
      try {
        window.localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify(themeParam));
      } catch (e) {
        console.warn('Failed to save theme preference to localStorage', e); 
      }
    } else {
      try {
        const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
        if (stored) {
          themePreference = JSON.parse(stored);
        }
      } catch (e) {
        console.warn('Failed to load theme preference from localStorage', e); 
      }
    }
    
    let isDarkMode = false;
    if (themePreference === 'Dark') {
      isDarkMode = true;
    } else if (themePreference === 'Light') {
      isDarkMode = false;
    } else {
      isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    }

    if (isDarkMode) {
      html.classList.add('cds--g90');
      html.classList.remove('cds--white');
    } else {
      html.classList.add('cds--white');
      html.classList.remove('cds--g90');
    }
  } catch (error) {}
})();
`;

  const { insertScriptTags } = useInsertScriptTags({
    componentOrHookName: 'ApplyThemeScript',
    scriptTags: [
      {
        type: 'text/javascript',
        textContent: darkModeScript,
      },
    ],
  });

  useEffect(() => {
    insertScriptTags();
  }, [insertScriptTags]);
}
