/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { MainContent } from '@i-am-bee/beeai-ui';
import type { PropsWithChildren } from 'react';

import { AppFooter } from './AppFooter';
import classes from './MainContentView.module.scss';

export function MainContentView({ children }: PropsWithChildren) {
  return (
    <MainContent className={classes.root}>
      {children}
      <AppFooter />
    </MainContent>
  );
}
