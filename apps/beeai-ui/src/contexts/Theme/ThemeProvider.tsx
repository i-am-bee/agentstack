/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

'use client';

import type { PropsWithChildren } from 'react';
import { useCallback, useEffect, useMemo } from 'react';
import { useLocalStorage, useMediaQuery } from 'usehooks-ts';

import { ThemeContext, ThemePreference } from './theme-context';
import { Theme } from './types';
import { getThemeClassName } from './utils';

const MEDIA_QUERY = '(prefers-color-scheme: dark)';
const STORAGE_KEY = '@i-am-bee/beeai/THEME';

export function ThemeProvider({ children }: PropsWithChildren) {
  const isDarkModeOS = useMediaQuery(MEDIA_QUERY);
  const [themePreference, setThemePreference] = useLocalStorage<ThemePreference>(STORAGE_KEY, ThemePreference.System);

  const isDarkMode =
    themePreference === ThemePreference.System ? isDarkModeOS : themePreference === ThemePreference.Dark;
  const theme = isDarkMode ? Theme.Dark : Theme.Light;

  const toggleTheme = useCallback(
    () =>
      setThemePreference((userTheme) => {
        const isDarkMode = userTheme === ThemePreference.System ? isDarkModeOS : userTheme === ThemePreference.Dark;
        return isDarkMode ? ThemePreference.Light : ThemePreference.Dark;
      }),
    [isDarkModeOS, setThemePreference],
  );

  useEffect(() => {
    const html = document.documentElement;

    html.classList.toggle(getThemeClassName(Theme.Dark), isDarkMode);
    html.classList.toggle(getThemeClassName(Theme.Light), !isDarkMode);
  }, [isDarkMode]);

  const contextValue = useMemo(
    () => ({ theme, themePreference, toggleTheme, setThemePreference }),
    [setThemePreference, theme, themePreference, toggleTheme],
  );

  return <ThemeContext.Provider value={contextValue}>{children}</ThemeContext.Provider>;
}
