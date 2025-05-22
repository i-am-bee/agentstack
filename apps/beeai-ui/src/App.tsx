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

import { ErrorBoundary } from 'react-error-boundary';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router';

import { ErrorFallback } from '#components/fallbacks/ErrorFallback.tsx';
import { AppLayout } from '#components/layouts/AppLayout.tsx';
import { ModalProvider } from '#contexts/Modal/ModalProvider.tsx';
import { QueryProvider } from '#contexts/QueryProvider/QueryProvider.tsx';
import { ThemeProvider } from '#contexts/Theme/ThemeProvider.tsx';
import { ToastProvider } from '#contexts/Toast/ToastProvider.tsx';
import { ComposeLanding } from '#modules/compose/ComposeLanding.tsx';
import { ComposeSequential } from '#modules/compose/ComposeSequential.tsx';
import { Agents } from '#pages/Agents.tsx';
import { Agent } from '#pages/agents/Agent.tsx';
import { NotFound } from '#pages/NotFound.tsx';
import { AgentRunPage } from '#pages/runs/AgentRunPage.tsx';
import { Settings } from '#pages/Settings.tsx';
import { routeDefinitions } from '#utils/router.ts';

export function App() {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <ToastProvider>
        <QueryProvider>
          <ThemeProvider>
            <ModalProvider>
              <BrowserRouter>
                <Routes>
                  <Route element={<AppLayout />}>
                    <Route
                      path={routeDefinitions.home()}
                      element={<Navigate to={routeDefinitions.agents()} replace />}
                    />
                    <Route path={routeDefinitions.agents()} element={<Agents />} />
                    <Route path={routeDefinitions.agentDetail()} element={<Agent />} />
                    <Route path={routeDefinitions.agentRun()} element={<AgentRunPage />} />
                    <Route path={routeDefinitions.playground()} element={<ComposeLanding />} />
                    <Route path={routeDefinitions.playgroundSequential()} element={<ComposeSequential />} />
                    <Route path={routeDefinitions.settings()} element={<Settings />} />

                    <Route path="*" element={<NotFound />} />
                  </Route>
                </Routes>
              </BrowserRouter>
            </ModalProvider>
          </ThemeProvider>
        </QueryProvider>
      </ToastProvider>
    </ErrorBoundary>
  );
}
