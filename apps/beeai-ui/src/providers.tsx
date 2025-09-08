/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { SessionProvider } from 'next-auth/react';
import type { PropsWithChildren } from 'react';

import { ModalProvider } from '#contexts/Modal/ModalProvider.tsx';
import { ProgressBarProvider } from '#contexts/ProgressBar/ProgressBarProvider.tsx';
import { QueryProvider } from '#contexts/QueryProvider/QueryProvider.tsx';
import { ThemeProvider } from '#contexts/Theme/ThemeProvider.tsx';
import { ToastProvider } from '#contexts/Toast/ToastProvider.tsx';
import { RouteTransitionProvider } from '#contexts/TransitionContext/RouteTransitionProvider.tsx';

export default function Providers({ children }: PropsWithChildren) {
  return (
    <SessionProvider>
      <ToastProvider>
        <QueryProvider>
          <ProgressBarProvider>
            <ThemeProvider>
              <RouteTransitionProvider>
                <ModalProvider>{children}</ModalProvider>
              </RouteTransitionProvider>
            </ThemeProvider>
          </ProgressBarProvider>
        </QueryProvider>
      </ToastProvider>
    </SessionProvider>
  );
}
