/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';
import z from 'zod';

import { useToast } from '#contexts/Toast/index.ts';

import { connectorKeys } from '../api/keys';
import { useConnectConnector } from '../api/mutations/useConnectConnector';
import { useDisconnectConnector } from '../api/mutations/useDisconnectConnector';

const authorizeOAuth = (
  url: string,
  onCallback: (props: { error: string | null; errorDescription: string | null }) => void,
) => {
  const popup = window.open(url);
  if (!popup) {
    throw new Error('Failed to open popup');
  }
  popup.focus();

  let isHandled = false;

  const timer = setInterval(() => {
    if (popup.closed) {
      clearInterval(timer);

      if (!isHandled) {
        onCallback({
          error: 'Authorization cancelled',
          errorDescription: 'Popup was closed before completing authorization.',
        });
      }

      window.removeEventListener('message', handler);
    }
  }, 500);

  function handler(message: unknown) {
    const { success, data: parsedMessage } = z
      .object({ data: z.object({ redirect_uri: z.string() }) })
      .safeParse(message);

    if (!success) {
      return;
    }

    const parsedRedirectrUri = new URL(parsedMessage.data.redirect_uri);
    const error = parsedRedirectrUri.searchParams.get('error');
    const errorDescription = parsedRedirectrUri.searchParams.get('error_description');

    isHandled = true;

    onCallback({ error, errorDescription });

    if (popup) {
      clearInterval(timer);
      window.removeEventListener('message', handler);
      popup.close();
    }
  }

  window.addEventListener('message', handler);
};

export const useDisconnect = () => {
  const { mutateAsync: disconnectConnector, isPending } = useDisconnectConnector();

  const disconnect = useCallback(
    async (connectorId: string) => {
      await disconnectConnector({ connector_id: connectorId });
    },
    [disconnectConnector],
  );

  return {
    disconnect,
    isPending,
  };
};

const useHandleAuthorizeCallback = () => {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  return useCallback(
    ({ error, errorDescription }: { error: string | null; errorDescription: string | null }) => {
      if (error) {
        addToast({
          kind: 'error',
          title: error,
          message: errorDescription ?? 'An unknown error occurred',
        });
      } else {
        queryClient.invalidateQueries({ queryKey: connectorKeys.list() });
      }
    },
    [addToast, queryClient],
  );
};

export const useConnect = () => {
  const [isAuthorizing, setIsAuthorizing] = useState(false);

  const { mutateAsync: connectConnector, isPending } = useConnectConnector();
  const handleAuthorizeCallback = useHandleAuthorizeCallback();

  const connect = useCallback(
    async (connectorId: string) => {
      const result = await connectConnector({ connector_id: connectorId });

      if (result?.auth_request) {
        setIsAuthorizing(true);
        authorizeOAuth(result.auth_request.authorization_endpoint, (props) => {
          handleAuthorizeCallback(props);
          setIsAuthorizing(false);
        });
      }
    },
    [connectConnector, handleAuthorizeCallback],
  );

  return {
    connect,
    isPending: isPending || isAuthorizing,
  };
};

export const useAuthorize = () => {
  const [isPending, setIsPending] = useState(false);

  const handleAuthorizeCallback = useHandleAuthorizeCallback();

  const authorize = useCallback(
    (authorizationEndpoint: string) => {
      setIsPending(true);
      authorizeOAuth(authorizationEndpoint, (props) => {
        handleAuthorizeCallback(props);
        setIsPending(false);
      });
    },
    [handleAuthorizeCallback],
  );

  return {
    authorize,
    isPending,
  };
};
