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
