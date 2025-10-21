/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import classes from './AppHeader.module.scss';
import { Container } from './Container';

export function AppHeader({ children }: PropsWithChildren) {
  return (
    <header className={classes.root}>
      <Container size="full">{children}</Container>
    </header>
  );
}
