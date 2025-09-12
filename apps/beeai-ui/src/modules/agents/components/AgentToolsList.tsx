/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Agent } from '../api/types';
import { AgentTool } from './AgentTool';
import classes from './AgentToolsList.module.scss';

interface Props {
  agent: Agent;
}

export function AgentToolsList({ agent }: Props) {
  const { tools } = agent.ui;

  return (
    <div className={classes.root}>
      {tools?.length ? (
        <ul className={classes.list}>
          {tools.map((tool, idx) => (
            <li key={idx}>
              <AgentTool tool={tool} />
            </li>
          ))}
        </ul>
      ) : (
        <p className={classes.empty}>This agent does not have any tools</p>
      )}
    </div>
  );
}
