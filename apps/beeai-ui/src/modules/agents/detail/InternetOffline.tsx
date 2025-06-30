/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ErrorFilled } from '@carbon/icons-react';

import { useIsOnline } from '#hooks/useIsOnline.ts';

import classes from './InternetOffline.module.scss';

export function InternetOffline() {
  const isOnline = useIsOnline();

  if (isOnline) {
    return null;
  }

  return (
    <span className={classes.root}>
      <ErrorFilled />

      <span>Internet offline</span>
    </span>
  );
}
