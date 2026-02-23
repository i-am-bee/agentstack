/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useApp } from '#contexts/App/index.ts';
import { SidePanelVariant } from '#contexts/App/types.ts';
import type { UISourcePart } from '#modules/messages/types.ts';
import { isNotNull } from '#utils/helpers.ts';

import { useSources } from '../contexts';
import { SourcesButton } from './SourcesButton';

interface Props {
  sources: UISourcePart[];
  taskId?: string;
  artifactId?: string;
}

export function SourcesGroup({ sources, taskId, artifactId }: Props) {
  const { activeSidePanel, openSidePanel, closeSidePanel } = useApp();
  const { activeSource, setActiveSource } = useSources();

  const hasSources = sources.length > 0;

  const isPanelOpen = activeSidePanel === SidePanelVariant.Sources;
  const isMessageActive =
    isNotNull(taskId) && taskId === activeSource?.taskId && activeSource?.artifactId === artifactId;
  const isActive = isPanelOpen && isMessageActive;

  const handleButtonClick = () => {
    if (isMessageActive) {
      if (isPanelOpen) {
        closeSidePanel();
      } else {
        openSidePanel(SidePanelVariant.Sources);
      }
    } else if (taskId) {
      setActiveSource({ number: null, taskId, artifactId });
      openSidePanel(SidePanelVariant.Sources);
    }
  };

  if (!hasSources) {
    return null;
  }

  return <SourcesButton sources={sources} isActive={isActive} onClick={handleButtonClick} />;
}
