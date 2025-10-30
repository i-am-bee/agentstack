/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { ProgressBarProvider, RouteTransitionProvider, ThemeProvider } from '@i-am-bee/agentstack-ui';
import { QueryClientProvider } from '@tanstack/react-query';
import type { PropsWithChildren } from 'react';

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
