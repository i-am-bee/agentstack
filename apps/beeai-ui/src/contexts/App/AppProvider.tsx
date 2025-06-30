/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
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
