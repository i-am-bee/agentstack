/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useApp } from '#contexts/App/index.ts';

import classes from './AppName.module.scss';

export function AppName() {
  const {
    config: { appName, companyName },
  } = useApp();

  return (
    <span className={classes.root}>
      {companyName && <span className={classes.companyName}>{companyName}</span>}

      <span className={classes.appName}>{appName}</span>
    </span>
  );
}
