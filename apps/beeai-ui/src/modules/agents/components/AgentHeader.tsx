/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import classes from './AgentHeader.module.scss';

export function AgentHeader({ children }: PropsWithChildren) {
  return <div className={classes.root}>{children}</div>;
}
