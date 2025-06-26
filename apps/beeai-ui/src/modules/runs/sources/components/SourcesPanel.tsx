/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Close } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import { useEffect } from 'react';

import { SidePanel } from '#components/SidePanel/SidePanel.tsx';
import { useApp } from '#contexts/App/index.ts';

import { useSources } from '../contexts';
import { SourcesList } from './SourcesList';
import classes from './SourcesPanel.module.scss';

export function SourcesPanel() {
  const { sourcesPanelOpen, hideSourcesPanel } = useApp();
  const { sourcesData, activeMessageKey } = useSources();

  const sources = activeMessageKey ? (sourcesData[activeMessageKey] ?? []) : [];
  const hasSources = sources.length > 0;

  useEffect(() => {
    if (!hasSources) {
      hideSourcesPanel?.();
    }
  }, [hasSources, hideSourcesPanel]);

  return (
    <SidePanel variant="right" isOpen={sourcesPanelOpen}>
      <div className={classes.root}>
        <header className={classes.header}>
          <h2 className={classes.heading}>Sources</h2>

          <IconButton
            size="sm"
            kind="ghost"
            label="Close"
            wrapperClasses={classes.closeButton}
            onClick={hideSourcesPanel}
          >
            <Close />
          </IconButton>
        </header>

        <SourcesList sources={sources} />
      </div>
    </SidePanel>
  );
}
