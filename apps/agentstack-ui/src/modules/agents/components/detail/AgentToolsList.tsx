/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { NoItemsMessage } from '#components/NoItemsMessage/NoItemsMessage.tsx';
import type { Agent } from '#modules/agents/api/types.ts';

import { AgentTool } from './AgentTool';
import classes from './AgentToolsList.module.scss';

interface Props {
  agent: Agent;
}

export function AgentToolsList({ agent }: Props) {
  const { tools } = agent.ui;

  const hasTools = !!tools && tools.length > 0;

  return (
    <div className={classes.root}>
      {hasTools ? (
        <ul className={classes.list}>
          {tools.map((tool, idx) => (
            <li key={idx}>
              <AgentTool tool={tool} />
            </li>
          ))}
        </ul>
      ) : (
        <NoItemsMessage message="This agent does not have any tools" />
      )}
    </div>
  );
}
