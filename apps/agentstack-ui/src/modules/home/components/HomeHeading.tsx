/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { useApp } from '#contexts/App/index.ts';

import classes from './HomeHeading.module.scss';

export function HomeHeading() {
  const {
    config: { appName },
  } = useApp();

  return <h1 className={classes.root}>Welcome to {appName}</h1>;
}
