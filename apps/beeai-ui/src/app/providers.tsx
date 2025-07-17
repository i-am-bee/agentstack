/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import type { PropsWithChildren } from 'react';

import { AppProvider } from '#contexts/App/AppProvider.tsx';
import { AppConfigProvider } from '#contexts/AppConfig/AppConfigProvider.tsx';
import { ModalProvider } from '#contexts/Modal/ModalProvider.tsx';
import { ProgressBarProvider } from '#contexts/ProgressBar/ProgressBarProvider.tsx';
import { QueryProvider } from '#contexts/QueryProvider/QueryProvider.tsx';
import { ThemeProvider } from '#contexts/Theme/ThemeProvider.tsx';
import { ToastProvider } from '#contexts/Toast/ToastProvider.tsx';
import { RouteTransitionProvider } from '#contexts/TransitionContext/RouteTransitionProvider.tsx';

export default function Providers({ children }: PropsWithChildren) {
  return (
    <ToastProvider>
      <ProgressBarProvider>
        <ThemeProvider>
          <RouteTransitionProvider>
            <QueryProvider>
              <ModalProvider>
                <AppConfigProvider>
                  <AppProvider>{children}</AppProvider>
                </AppConfigProvider>
              </ModalProvider>
            </QueryProvider>
          </RouteTransitionProvider>
        </ThemeProvider>
      </ProgressBarProvider>
    </ToastProvider>
  );
}
