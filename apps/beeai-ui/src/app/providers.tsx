/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { QueryClientProvider } from '@tanstack/react-query';
import type { PropsWithChildren } from 'react';

import { AppProvider } from '#contexts/App/AppProvider.tsx';
import { ModalProvider } from '#contexts/Modal/ModalProvider.tsx';
import { ProgressBarProvider } from '#contexts/ProgressBar/ProgressBarProvider.tsx';
import { ThemeProvider } from '#contexts/Theme/ThemeProvider.tsx';
import { ToastProvider } from '#contexts/Toast/ToastProvider.tsx';
import { RouteTransitionProvider } from '#contexts/TransitionContext/RouteTransitionProvider.tsx';
import { FeatureFlags } from '#utils/feature-flags.ts';

interface Props {
  featureFlags: FeatureFlags;
}

export default function Providers({ featureFlags, children }: PropsWithChildren<Props>) {
  return (
    <ToastProvider>
      <QueryProvider>
        <ProgressBarProvider>
          <ThemeProvider>
            <RouteTransitionProvider>
              <ModalProvider>
                <AppProvider featureFlags={featureFlags}>{children}</AppProvider>
              </ModalProvider>
            </RouteTransitionProvider>
          </ThemeProvider>
        </ProgressBarProvider>
      </QueryProvider>
    </ToastProvider>
  );
}
