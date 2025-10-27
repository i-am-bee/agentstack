/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { TextInput } from '@carbon/react';
import { useId } from 'react';

import { useAgentDemands } from '../contexts/agent-demands';
import classes from './MCPConfig.module.scss';

/**
 * This component is for testing purposes only
 */
export function MCPConfig() {
  const id = useId();
  const { selectedMCPServers, selectMCPServer } = useAgentDemands();

  const entries = Object.entries(selectedMCPServers);
  if (!entries.length) {
    return null;
  }

  return (
    <div className={classes.root}>
      {entries.map(([key, value]) => (
        <TextInput
          value={value}
          onChange={(e) => selectMCPServer(key, e.target.value)}
          id={`${id}:${key}`}
          labelText={`MCP: ${key}`}
          key={key}
          inline
        />
      ))}
    </div>
  );
}
