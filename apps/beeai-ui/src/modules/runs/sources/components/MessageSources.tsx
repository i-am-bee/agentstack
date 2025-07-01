/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback } from 'react';

import { useApp } from '#contexts/App/index.ts';
import type { AgentMessage } from '#modules/runs/chat/types.ts';

import { useSources } from '../contexts';
import { SourcesButton } from './SourcesButton';

interface Props {
  message: AgentMessage;
}

export function MessageSources({ message }: Props) {
  const { sourcesPanelOpen, showSourcesPanel, hideSourcesPanel } = useApp();
  const { activeMessageKey, setActiveMessageKey, setActiveSourceKey } = useSources();

  const messageKey = message.key;
  const sources = message.sources ?? [];
  const hasSources = sources.length > 0;

  const isActive = sourcesPanelOpen && messageKey === activeMessageKey;

  const handleButtonClick = useCallback(() => {
    if (messageKey === activeMessageKey) {
      if (sourcesPanelOpen) {
        hideSourcesPanel?.();
      } else {
        showSourcesPanel?.();
      }
    } else {
      setActiveMessageKey?.(messageKey);
      setActiveSourceKey?.(null);
      showSourcesPanel?.();
    }
  }, [
    messageKey,
    activeMessageKey,
    sourcesPanelOpen,
    hideSourcesPanel,
    showSourcesPanel,
    setActiveMessageKey,
    setActiveSourceKey,
  ]);

  return hasSources ? <SourcesButton sources={sources} isActive={isActive} onClick={handleButtonClick} /> : null;
}
