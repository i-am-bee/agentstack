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
import { useState } from 'react';

import { SidePanel } from '#components/SidePanel/SidePanel.tsx';

import { SourcesList } from './SourcesList';
import classes from './SourcesPanel.module.scss';

export function SourcesPanel() {
  const [isOpen, setIsOpen] = useState(true);
  // TODO
  const sources = [
    {
      number: 1,
      url: 'https://research.ibm.com/projects/bee-ai-platform',
    },
    {
      number: 2,
      url: 'https://research.ibm.com/projects/bee-ai-platform',
    },
    {
      number: 3,
      url: 'https://research.ibm.com/projects/bee-ai-platform',
    },
    {
      number: 4,
      url: 'https://research.ibm.com/projects/bee-ai-platform',
    },
  ];

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
            onClick={() => setIsOpen(false)}
          >
            <Close />
          </IconButton>
        </header>

        <SourcesList sources={sources} />
      </div>
    </SidePanel>
  );
}
