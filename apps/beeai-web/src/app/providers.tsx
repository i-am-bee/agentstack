/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { ThemeProvider } from '@i-am-bee/beeai-ui';
import { QueryClientProvider } from '@tanstack/react-query';
import { PropsWithChildren } from 'react';

import { ProgressBarProvider } from '../../../beeai-ui/src/contexts/ProgressBar/ProgressBarProvider';
import { RouteTransitionProvider } from '../../../beeai-ui/src/contexts/TransitionContext/RouteTransitionProvider';
import { getQueryClient } from './get-query-client';

export default function Providers({ children }: PropsWithChildren) {
  const queryClient = getQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <ProgressBarProvider>
        <ThemeProvider>
          <RouteTransitionProvider>{children}</RouteTransitionProvider>
        </ThemeProvider>
      </ProgressBarProvider>
    </QueryClientProvider>
  );
}
