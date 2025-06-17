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

import { SidePanel } from '#components/SidePanel/SidePanel.tsx';

import type { SourceReference } from '../api/types';
import { useSources } from '../contexts';
import { SourcesList } from './SourcesList';
import classes from './SourcesPanel.module.scss';

interface Props {
  sources: SourceReference[];
}

export function SourcesPanel({ sources }: Props) {
  const { activeMessage, hideSources } = useSources();
  const isOpen = Boolean(activeMessage);

  return (
    <SidePanel variant="right" isOpen={isOpen}>
      <div className={classes.root}>
        <header className={classes.header}>
          <h2 className={classes.heading}>Sources</h2>

          <IconButton size="sm" kind="ghost" label="Close" wrapperClasses={classes.closeButton} onClick={hideSources}>
            <Close />
          </IconButton>
        </header>

        <SourcesList sources={sources} />
      </div>
    </SidePanel>
  );
}
