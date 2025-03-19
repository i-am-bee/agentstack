/**
 * Copyright 2025 IBM Corp.
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

import type { Agent } from '#modules/agents/api/types.ts';
import { IconButton } from '@carbon/react';
import clsx from 'clsx';
import { AgentIcon } from '../components/AgentIcon';
import classes from './AgentHeader.module.scss';
import NewSession from './NewSession.svg';

interface Props {
  agent: Agent;
  onNewSessionClick?: () => void;
  className?: string;
}

export function AgentHeader({ agent, onNewSessionClick, className }: Props) {
  return (
    <header className={clsx(classes.root, className)}>
      <h1 className={classes.heading}>
        <AgentIcon />

        <span className={classes.name}>{agent.name}</span>
      </h1>

      {onNewSessionClick && (
        <IconButton kind="tertiary" size="sm" label="New session" autoAlign onClick={onNewSessionClick}>
          <NewSession />
        </IconButton>
      )}
    </header>
  );
}
