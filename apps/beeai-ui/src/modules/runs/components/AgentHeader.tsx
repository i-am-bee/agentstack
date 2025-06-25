/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { IconButton } from '@carbon/react';
import clsx from 'clsx';

import type { Agent } from '#modules/agents/api/types.ts';
import { getAgentUiMetadata } from '#modules/agents/utils.ts';
import { isNotNull } from '#utils/helpers.ts';

import { AgentIcon } from '../components/AgentIcon';
import classes from './AgentHeader.module.scss';
import NewSession from './NewSession.svg';

interface Props {
  agent?: Agent;
  onNewSessionClick?: () => void;
  className?: string;
}

export function AgentHeader({ agent, onNewSessionClick, className }: Props) {
  const { display_name } = agent ? getAgentUiMetadata(agent) : {};
  const showAgent = isNotNull(agent) && isNotNull(display_name);

  return (
    <header className={clsx(classes.root, className)}>
      <div>
        {showAgent && (
          <h1 className={classes.heading}>
            <AgentIcon inverted />

            <span className={classes.name}>{display_name}</span>
          </h1>
        )}
      </div>

      {onNewSessionClick && (
        <IconButton kind="tertiary" size="sm" label="New session" align="left" autoAlign onClick={onNewSessionClick}>
          <NewSession />
        </IconButton>
      )}
    </header>
  );
}
