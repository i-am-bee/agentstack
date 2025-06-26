/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import classes from './ViewStack.module.scss';

export function ViewStack({ children }: PropsWithChildren) {
  return <div className={classes.root}>{children}</div>;
}
