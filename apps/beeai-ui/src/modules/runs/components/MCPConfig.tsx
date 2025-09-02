/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useApp } from '#contexts/App/index.ts';
import { usePlatformContext } from '#modules/platform-context/contexts/index.ts';

export function MCPConfig() {
  const { featureFlags } = useApp();
  const { selectedMCPServers, selectMCPServer } = usePlatformContext();

  return (
    featureFlags.MCP && (
      <>
        MCP Config:
        <div>
          {Object.entries(selectedMCPServers).map(([key, value]) => (
            <div key={key}>
              {key}: <input type="text" value={value} onChange={(e) => selectMCPServer(key, e.target.value)} />
            </div>
          ))}
        </div>
      </>
    )
  );
}
