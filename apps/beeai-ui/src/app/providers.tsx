/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { QueryClientProvider } from '@tanstack/react-query';
import type { PropsWithChildren } from 'react';

import { AppProvider } from '#contexts/App/AppProvider.tsx';
import { AppConfigProvider } from '#contexts/AppConfig/AppConfigProvider.tsx';
import { ModalProvider } from '#contexts/Modal/ModalProvider.tsx';
import { ProgressBarProvider } from '#contexts/ProgressBar/ProgressBarProvider.tsx';
import { ThemeProvider } from '#contexts/Theme/ThemeProvider.tsx';
import { ToastProvider } from '#contexts/Toast/ToastProvider.tsx';
import { RouteTransitionProvider } from '#contexts/TransitionContext/RouteTransitionProvider.tsx';
import { FeatureFlags } from '#utils/feature-flags.ts';

import { getQueryClient } from './get-query-client';

interface Props {
  featureFlags: FeatureFlags;
}

export default function Providers({ featureFlags, children }: PropsWithChildren<Props>) {
  const queryClient = getQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <ProgressBarProvider>
        <ThemeProvider>
          <RouteTransitionProvider>
            <ToastProvider>
              <ModalProvider>
                <AppConfigProvider featureFlags={featureFlags}>
                  <AppProvider>{children}</AppProvider>
                </AppConfigProvider>
              </ModalProvider>
            </ToastProvider>
          </RouteTransitionProvider>
        </ThemeProvider>
      </ProgressBarProvider>
    </QueryClientProvider>
  );
}
