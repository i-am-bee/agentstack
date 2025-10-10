/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import classes from './AgentName.module.scss';

export function AgentName({ children }: PropsWithChildren) {
  return <h1 className={classes.root}>{children}</h1>;
}
