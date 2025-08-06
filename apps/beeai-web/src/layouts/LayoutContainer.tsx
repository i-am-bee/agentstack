/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Container } from '@i-am-bee/beeai-ui';
import type { PropsWithChildren } from 'react';

import classes from './LayoutContainer.module.scss';

interface Props {
  asGrid?: boolean;
  className?: string;
}

export function LayoutContainer({ asGrid, className, children }: PropsWithChildren<Props>) {
  return (
    <Container size="max" className={className}>
      <div className={classes.grid}>{asGrid ? children : <div className={classes.content}>{children}</div>}</div>
    </Container>
  );
}
