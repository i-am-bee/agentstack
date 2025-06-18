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

import type { PropsWithChildren } from 'react';
import { useCallback, useMemo, useState } from 'react';

import { AppContext } from './app-context';

export function AppProvider({ children }: PropsWithChildren) {
  const [navigationOpen, setNavigationOpen] = useState(false);
  const [agentDetailOpen, setAgentDetailOpen] = useState(false);
  const [sourcesPanelOpen, setSourcesPanelOpen] = useState(false);
  const [closeNavOnClickOutside, setCloseNavOnClickOutside] = useState(false);

  const hideSourcesPanel = useCallback(() => {
    setSourcesPanelOpen(false);
  }, []);

  const showAgentDetail = useCallback(() => {
    setAgentDetailOpen(true);
    hideSourcesPanel();
  }, [hideSourcesPanel]);

  const hideAgentDetail = useCallback(() => {
    setAgentDetailOpen(false);
  }, []);

  const showSourcesPanel = useCallback(() => {
    setSourcesPanelOpen(true);
    hideAgentDetail();
  }, [hideAgentDetail]);

  const contextValue = useMemo(
    () => ({
      navigationOpen,
      agentDetailOpen,
      sourcesPanelOpen,
      closeNavOnClickOutside,
      setNavigationOpen,
      showAgentDetail,
      hideAgentDetail,
      showSourcesPanel,
      hideSourcesPanel,
      setCloseNavOnClickOutside,
    }),
    [
      navigationOpen,
      agentDetailOpen,
      sourcesPanelOpen,
      closeNavOnClickOutside,
      showAgentDetail,
      hideAgentDetail,
      showSourcesPanel,
      hideSourcesPanel,
    ],
  );

  return <AppContext.Provider value={contextValue}>{children}</AppContext.Provider>;
}
