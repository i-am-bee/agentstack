/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback } from 'react';
import { useCreateConnector } from '../api/mutations/useCreateConnector';
import { useListConnectors } from '../api/queries/useListConnectors';
import { useConnectConnector } from '../api/mutations/useConnectConnector';

export const OAuthConnectorsView = () => {
  const { mutate: createConnector, isPending: isCreating } = useCreateConnector();
  const { mutate: connectConnector, isPending: isConnecting } = useConnectConnector();

  const { data: connectors } = useListConnectors();

  const addConnector = useCallback(() => {
    createConnector({
      url: 'http://api.githubcopilot.com/mcp',
      client_id: '',
      client_secret: '',
    });
  }, [createConnector]);

  const connect = useCallback(
    async (connectorId: string) => {
      const result = await connectConnector(connectorId);
      console.log(result);
    },
    [connectConnector],
  );

  return (
    <div>
      <button onClick={addConnector} disabled={isCreating}>
        {isCreating ? 'Adding...' : 'Add Connector'}
      </button>

      {connectors &&
        connectors.items.map((connector) => (
          <div key={connector.id}>
            {connector.url} - {connector.state} <button onClick={() => connect(connector.id)}>Connect</button>
          </div>
        ))}
    </div>
  );
};
