/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback } from 'react';

import { useApp } from '#contexts/App/index.ts';
import { SidePanelVariant } from '#contexts/App/types.ts';
import type { UIAgentMessage } from '#modules/messages/types.ts';
import { getMessageSources } from '#modules/messages/utils.ts';
import { isNotNull } from '#utils/helpers.ts';

import { useSources } from '../contexts';
import { SourcesButton } from './SourcesButton';

interface Props {
  message: UIAgentMessage;
}

export function MessageSources({ message }: Props) {
  const { activeSidePanel, openSidePanel, closeSidePanel } = useApp();
  const { activeSource, setActiveSource } = useSources();

  const { taskId } = message;
  const sources = getMessageSources(message);
  const hasSources = sources.length > 0;

  const isPanelOpen = activeSidePanel === SidePanelVariant.Sources;
  const isMessageActive = isNotNull(taskId) && taskId === activeSource?.taskId;
  const isActive = isPanelOpen && isMessageActive;

  const handleButtonClick = useCallback(() => {
    if (isMessageActive) {
      if (isPanelOpen) {
        closeSidePanel();
      } else {
        openSidePanel(SidePanelVariant.Sources);
      }
    } else if (taskId) {
      setActiveSource({ number: null, taskId });
      openSidePanel(SidePanelVariant.Sources);
    }
  }, [isMessageActive, isPanelOpen, taskId, openSidePanel, closeSidePanel, setActiveSource]);

  if (!hasSources) {
    return null;
  }

  return <SourcesButton sources={sources} isActive={isActive} onClick={handleButtonClick} />;
}
