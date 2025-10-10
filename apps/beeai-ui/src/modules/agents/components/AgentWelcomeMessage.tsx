/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import classes from './AgentWelcomeMessage.module.scss';

export function AgentWelcomeMessage({ children }: PropsWithChildren) {
  return <p className={classes.root}>{children}</p>;
}
