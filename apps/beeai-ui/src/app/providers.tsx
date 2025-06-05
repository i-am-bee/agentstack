/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
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

import { getQueryClient } from './get-query-client';

export default function Providers({ children }: PropsWithChildren) {
  const queryClient = getQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <ProgressBarProvider>
        <ThemeProvider>
          <RouteTransitionProvider>
            <ToastProvider>
              <ModalProvider>
                <AppConfigProvider>
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
