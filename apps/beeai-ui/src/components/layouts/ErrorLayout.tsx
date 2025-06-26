/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import { Container } from './Container';
import classes from './ErrorLayout.module.scss';

export function ErrorLayout({ children }: PropsWithChildren) {
  return (
    <div className={classes.root}>
      <Container>{children}</Container>
    </div>
  );
}
