/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, InlineLoading } from '@carbon/react';
import clsx from 'clsx';
import { useCallback, useMemo } from 'react';

import { useCreateConnector } from '../api/mutations/useCreateConnector';
import { useListConnectors } from '../api/queries/useListConnectors';
import type { ConnectorPreset } from '../api/types';
import { useConnect, useDisconnect } from '../hooks/useConnectors';
import classes from './ConnectPresetButton.module.scss';

interface Props {
  preset: ConnectorPreset;
  className: string;
}

export function ConnectPresetButton({ preset, className }: Props) {
  const { url } = preset;

  const { data: connectors, isPending: isConnectorsPending } = useListConnectors();
  const { mutate: createConnector, isPending: isCreatePending } = useCreateConnector({
    onSuccess: ({ id }) => connect(id),
  });
  const { connect, isPending: isConnectPending } = useConnect();
  const { disconnect, isPending: isDisconnectPending } = useDisconnect();

  const connector = useMemo(
    () => connectors?.items.find((connector) => connector.url === url),
    [connectors?.items, url],
  );

  const handleClick = useCallback(() => {
    if (connector) {
      if (connector.state === 'connected') {
        disconnect(connector.id);
      } else {
        connect(connector.id);
      }
    } else {
      createConnector({ url, match_preset: true });
    }
  }, [connector, url, createConnector, connect, disconnect]);

  const isPending = isCreatePending || isConnectPending || isDisconnectPending;

  if (isConnectorsPending) {
    return null;
  }

  return (
    <Button
      kind="secondary"
      size="xs"
      className={clsx(classes.root, className)}
      disabled={isPending}
      onClick={handleClick}
    >
      {isPending ? (
        <InlineLoading description={`${isDisconnectPending ? 'Disconnecting' : 'Connecting'}…`} />
      ) : connector?.state === 'connected' ? (
        'Disconnect'
      ) : (
        'Connect'
      )}
    </Button>
  );
}
