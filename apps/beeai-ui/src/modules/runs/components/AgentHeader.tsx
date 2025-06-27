/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Agent } from '#modules/agents/api/types.ts';
import { AgentHeading } from '#modules/agents/components/AgentHeading.tsx';
import { isNotNull } from '#utils/helpers.ts';

import classes from './AgentHeader.module.scss';
import { NewSessionButton } from './NewSessionButton';

interface Props {
  agent?: Agent;
  onNewSessionClick?: () => void;
}

export function AgentHeader({ agent, onNewSessionClick }: Props) {
  const showAgent = isNotNull(agent);

  return (
    <header className={classes.root}>
      <div>{showAgent && <AgentHeading agent={agent} />}</div>

      {onNewSessionClick && <NewSessionButton onClick={onNewSessionClick} />}
    </header>
  );
}
