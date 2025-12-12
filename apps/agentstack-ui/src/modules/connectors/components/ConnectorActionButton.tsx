/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { CarbonIconType } from '@carbon/icons-react';
import { Credentials, Link, Unlink } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import { ConnectorState } from 'agentstack-sdk';
import { useMemo } from 'react';
import { match } from 'ts-pattern';

import { Spinner } from '#components/Spinner/Spinner.tsx';

import type { Connector } from '../api/types';
import { useAuthorize, useConnect, useDisconnect } from '../hooks/useConnectors';

interface Props {
  connector: Connector;
}

export function ConnectorActionButton({ connector }: Props) {
  const { id, state, auth_request } = connector;

  const { connect, isPending: isConnectPending } = useConnect();
  const { disconnect, isPending: isDisconnectPending } = useDisconnect();
  const { authorize, isPending: isAuthorizePending } = useAuthorize();

  const isPending = isConnectPending || isDisconnectPending || isAuthorizePending;

  const button: ButtonProps | null = useMemo(() => {
    const connectButton = {
      label: 'Connect',
      Icon: Link,
      onClick: () => connect(id),
    };

    const disconnectButton = {
      label: 'Disconnect',
      Icon: Unlink,
      onClick: () => disconnect(id),
    };

    const authorizeButton = auth_request
      ? {
          label: 'Authorize',
          Icon: Credentials,
          onClick: () => authorize(auth_request.authorization_endpoint),
        }
      : null;

    return match(state)
      .with(ConnectorState.Created, () => connectButton)
      .with(ConnectorState.Disconnected, () => connectButton)
      .with(ConnectorState.Connected, () => disconnectButton)
      .with(ConnectorState.AuthRequired, () => authorizeButton)
      .exhaustive();
  }, [id, state, auth_request, connect, disconnect, authorize]);

  if (!button) {
    return null;
  }

  const { Icon, ...buttonProps } = button;

  return (
    <IconButton {...buttonProps} kind="ghost" size="sm" align="left" disabled={isPending}>
      {isPending ? <Spinner center /> : <Icon />}
    </IconButton>
  );
}

type ButtonProps = {
  label: string;
  Icon: CarbonIconType;
  onClick: () => void;
};
