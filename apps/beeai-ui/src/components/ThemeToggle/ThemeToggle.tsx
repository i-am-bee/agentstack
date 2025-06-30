/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { Asleep, Awake } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import { useEffect, useState } from 'react';

import { useTheme } from '#contexts/Theme/index.ts';
import { Theme } from '#contexts/Theme/types.ts';

import classes from './ThemeToggle.module.scss';

export function ThemeToggle() {
  const [mounted, setMounted] = useState(false);
  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    setMounted(true);
  }, []);

  return mounted ? (
    <IconButton wrapperClasses={classes.root} kind="ghost" size="sm" label="Toggle theme" onClick={toggleTheme}>
      {theme === Theme.Light ? <Awake /> : <Asleep />}
    </IconButton>
  ) : null;
}
