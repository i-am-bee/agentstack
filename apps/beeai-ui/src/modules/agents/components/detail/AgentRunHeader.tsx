/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import classes from './AgentRunHeader.module.scss';

interface Props extends PropsWithChildren {
  heading?: string;
}

export function AgentRunHeader({ heading, children }: Props) {
  return (
    <div className={classes.root}>
      {heading && <h1 className={classes.heading}>{heading}</h1>}

      {children}
    </div>
  );
}
