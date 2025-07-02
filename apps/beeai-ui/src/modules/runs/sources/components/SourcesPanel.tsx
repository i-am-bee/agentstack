/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Close } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import { useEffect } from 'react';

import { SidePanel } from '#components/SidePanel/SidePanel.tsx';
import { useApp } from '#contexts/App/index.ts';
import { SidePanelVariant } from '#contexts/App/types.ts';

import { useSources } from '../contexts';
import { SourcesList } from './SourcesList';
import classes from './SourcesPanel.module.scss';

export function SourcesPanel() {
  const { activeSidePanel, closeSidePanel } = useApp();
  const { sourcesData, activeSource } = useSources();

  const messageKey = activeSource?.messageKey;
  const sources = messageKey ? (sourcesData[messageKey] ?? []) : [];
  const hasSources = sources.length > 0;

  const isOpen = activeSidePanel === SidePanelVariant.Sources;

  useEffect(() => {
    if (!hasSources) {
      closeSidePanel();
    }
  }, [hasSources, closeSidePanel]);

  return (
    <SidePanel variant="right" isOpen={isOpen}>
      <div className={classes.root}>
        <header className={classes.header}>
          <h2 className={classes.heading}>Sources</h2>

          <IconButton
            size="sm"
            kind="ghost"
            label="Close"
            wrapperClasses={classes.closeButton}
            onClick={closeSidePanel}
          >
            <Close />
          </IconButton>
        </header>

        <SourcesList sources={sources} />
      </div>
    </SidePanel>
  );
}
