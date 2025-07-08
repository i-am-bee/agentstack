/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback } from 'react';

import { useApp } from '#contexts/App/index.ts';
import { SidePanelVariant } from '#contexts/App/types.ts';
import type { AgentMessage } from '#modules/runs/chat/types.ts';

import { useSources } from '../contexts';
import { SourcesButton } from './SourcesButton';

interface Props {
  message: AgentMessage;
}

export function MessageSources({ message }: Props) {
  const { activeSidePanel, openSidePanel, closeSidePanel } = useApp();
  const { activeSource, setActiveSource } = useSources();

  const messageKey = message.key;
  const sources = message.sources ?? [];
  const hasSources = sources.length > 0;

  const isPanelOpen = activeSidePanel === SidePanelVariant.Sources;
  const isMessageActive = messageKey === activeSource?.messageKey;
  const isActive = isPanelOpen && isMessageActive;

  const handleButtonClick = useCallback(() => {
    if (isMessageActive) {
      if (isPanelOpen) {
        closeSidePanel();
      } else {
        openSidePanel(SidePanelVariant.Sources);
      }
    } else {
      setActiveSource({ key: null, messageKey });
      openSidePanel(SidePanelVariant.Sources);
    }
  }, [isMessageActive, isPanelOpen, messageKey, openSidePanel, closeSidePanel, setActiveSource]);

  return hasSources ? <SourcesButton sources={sources} isActive={isActive} onClick={handleButtonClick} /> : null;
}
