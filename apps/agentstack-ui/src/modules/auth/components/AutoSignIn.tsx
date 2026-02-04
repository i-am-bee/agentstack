/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { useEffect } from 'react';

import { useTheme } from '#contexts/Theme/index.ts';
import type { ThemePreference } from '#contexts/Theme/theme-context.ts';

interface Props {
  signIn: (theme: ThemePreference) => Promise<void>;
}

export function AutoSignIn({ signIn }: Props) {
  const { themePreference } = useTheme();

  useEffect(() => {
    void signIn(themePreference);
  }, [signIn, themePreference]);
  return <div>Redirecting to login...</div>;
}
