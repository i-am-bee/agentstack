/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback } from 'react';
import { match } from 'ts-pattern';

import { useCreateConnector } from '../api/mutations/useCreateConnector';
import { useListConnectors } from '../api/queries/useListConnectors';
import { useAuthorize, useConnect, useDisconnect, useRemove } from '../hooks/useConnectors';
import { AddConnectorForm, type CreateConnectorForm } from './AddConnectorForm';

export const ConnectorsView = () => {
  const { mutate: createConnector, isPending: isCreating } = useCreateConnector();
  const { data: connectors } = useListConnectors();
  const remove = useRemove();
  const disconnect = useDisconnect();
  const connect = useConnect();
  const authorize = useAuthorize();

  const onSubmit = useCallback(
    (data: CreateConnectorForm) => {
      createConnector({
        url: data.url,
        client_id: data.client_id,
        client_secret: data.client_secret,
      });
    },
    [createConnector],
  );

  return (
    <div>
      <AddConnectorForm onSubmit={onSubmit} isPending={isCreating} />

      {connectors &&
        connectors.items.map((connector) => (
          <div key={connector.id}>
            {connector.url}

            {match(connector)
              .with({ state: 'created' }, () => <button onClick={() => connect(connector.id)}>Connect</button>)
              .with({ state: 'connected' }, () => <button onClick={() => disconnect(connector.id)}>Disconnect</button>)
              .with({ state: 'disconnected' }, () => <button onClick={() => connect(connector.id)}>Connect</button>)
              .with({ state: 'auth_required' }, (connector) => (
                <button onClick={() => authorize(connector.auth_request.authorization_endpoint)}>Authorize</button>
              ))
              .exhaustive()}
            <button onClick={() => remove(connector.id)}>Remove</button>
          </div>
        ))}
    </div>
  );
};
