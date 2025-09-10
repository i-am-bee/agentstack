/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { TextInput } from '@carbon/react';
import { useId } from 'react';

import { usePlatformContext } from '#modules/platform-context/contexts/index.ts';

import classes from './MCPConfig.module.scss';

/**
 * This component is for testing purposes only
 */
export function MCPConfig() {
  const id = useId();
  const { selectedMCPServers, selectMCPServer } = usePlatformContext();

  return (
    <div className={classes.root}>
      {Object.entries(selectedMCPServers).map(([key, value]) => (
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
