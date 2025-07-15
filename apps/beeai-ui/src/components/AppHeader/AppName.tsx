/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { APP_NAME } from '#utils/constants.ts';

import classes from './AppName.module.scss';

export function AppName() {
  return <span className={classes.appName}>{APP_NAME}</span>;
}
