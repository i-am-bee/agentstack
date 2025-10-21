/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { useApp } from '#contexts/App/index.ts';

import classes from './SignInHeading.module.scss';

export function SignInHeading() {
  const {
    config: { appName },
  } = useApp();

  return (
    <h1 className={classes.root}>
      Log in to <strong>{appName}</strong>
    </h1>
  );
}
