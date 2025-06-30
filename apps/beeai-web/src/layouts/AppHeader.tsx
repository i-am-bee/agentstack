/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Container } from '@i-am-bee/beeai-ui';
import clsx from 'clsx';
import type { PropsWithChildren } from 'react';

import classes from './AppHeader.module.scss';

interface Props {
  className?: string;
}

export function AppHeader({ className, children }: PropsWithChildren<Props>) {
  return (
    <header className={clsx(classes.root, className)}>
      <Container size="max">
        <div className={classes.holder}>{children}</div>
      </Container>
    </header>
  );
}
