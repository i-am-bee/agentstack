/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import { createContext } from 'react';

import type { Theme } from './types';

export const ThemeContext = createContext<ThemeContextValue>({} as ThemeContextValue);

interface ThemeContextValue {
  theme: Theme;
  themePreference: ThemePreference;
  toggleTheme: () => void;
  setThemePreference: (theme: ThemePreference) => void;
}

export enum ThemePreference {
  System = 'System',
  Dark = 'Dark',
  Light = 'Light',
}
