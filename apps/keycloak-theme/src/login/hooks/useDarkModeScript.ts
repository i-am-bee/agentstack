/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useInsertScriptTags } from 'keycloakify/tools/useInsertScriptTags';
import { useEffect } from 'react';

const THEME_STORAGE_KEY = '@i-am-bee/agentstack/THEME';

/**
 * Injects dark mode script to prevent flash of wrong theme.
 * This must run as early as possible in the page lifecycle.
 */
export function useDarkModeScript() {
  const darkModeScript = `
(() => {
  try {
    const html = document.documentElement;
    const storedTheme = window.localStorage.getItem('${THEME_STORAGE_KEY}');
    const theme = typeof storedTheme === 'string' ? JSON.parse(storedTheme) : 'System';
    const isDarkMode = theme === 'Dark' || (theme === 'System' && window.matchMedia('(prefers-color-scheme: dark)').matches);

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
    componentOrHookName: 'DarkModeScript',
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
