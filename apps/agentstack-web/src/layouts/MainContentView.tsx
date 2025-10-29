/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { MainContentProps } from '@i-am-bee/beeai-ui';
import { MainContent } from '@i-am-bee/beeai-ui';
import type { PropsWithChildren } from 'react';

import { AppFooter } from './AppFooter';

interface Props extends PropsWithChildren {
  spacing?: MainContentProps['spacing'];
}

export function MainContentView({ spacing, children }: Props) {
  return (
    <MainContent spacing={spacing} footer={<AppFooter />}>
      {children}
    </MainContent>
  );
}
