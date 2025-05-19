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

import { Information } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';

import { useApp } from '#contexts/App/index.ts';

import classes from './AgentDetailButton.module.scss';

export function AgentDetailButton() {
  const { setAgentDetailOpen } = useApp();

  return (
    <IconButton
      kind="tertiary"
      size="sm"
      label="Agent Detail"
      wrapperClasses={classes.root}
      onClick={() => setAgentDetailOpen?.((value) => !value)}
    >
      <Information />
    </IconButton>
  );
}
