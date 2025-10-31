/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';
import z from 'zod';

import { useToast } from '#contexts/Toast/index.ts';

import { connectorKeys } from '../api/keys';
import { useConnectConnector } from '../api/mutations/useConnectConnector';
import { useDeleteConnector } from '../api/mutations/useDeleteConnector';
import { useDisconnectConnector } from '../api/mutations/useDisconnectConnector';

const authorizeOauth = (
  url: string,
  onCallback: (props: { error: string | null; errorDescription: string | null }) => void,
) => {
  const popup = window.open(url);
  if (!popup) {
    throw new Error('Failed to open popup');
  }
  popup.focus();

  const timer = setInterval(() => {
    if (popup.closed) {
      clearInterval(timer);
      window.removeEventListener('message', handler);
    }
  }, 500);

  async function handler(message: unknown) {
    const { success, data: parsedMessage } = z
      .object({ data: z.object({ redirect_uri: z.string() }) })
      .safeParse(message);

    if (!success) {
      throw new Error('Invalid message');
    }

    const url = new URL(parsedMessage.data.redirect_uri);
    const error = url.searchParams.get('error');
    const errorDescription = url.searchParams.get('error_description');

    onCallback({ error, errorDescription });

    if (popup) {
      window.removeEventListener('message', handler);
      popup.close();
    }
  }

  window.addEventListener('message', handler);
};

export const useRemove = () => {
  const { mutateAsync: removeConnector } = useDeleteConnector();

  return useCallback(
    async (connectorId: string) => {
      await removeConnector(connectorId);
    },
    [removeConnector],
  );
};

export const useDisconnect = () => {
  const { mutateAsync: disconnectConnector } = useDisconnectConnector();

  return useCallback(
    async (connectorId: string) => {
      await disconnectConnector(connectorId);
    },
    [disconnectConnector],
  );
};

const useHandleAuthorizeCallback = () => {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  return useCallback(
    ({ error, errorDescription }: { error: string | null; errorDescription: string | null }) => {
      if (error) {
        addToast({
          title: error,
          subtitle: errorDescription ?? 'An unknown error occurred',
        });
      } else {
        queryClient.invalidateQueries({ queryKey: connectorKeys.list() });
      }
    },
    [addToast, queryClient],
  );
};

export const useConnect = () => {
  const { mutateAsync: connectConnector } = useConnectConnector();
  const handleAuthorizeCallback = useHandleAuthorizeCallback();

  return useCallback(
    async (connectorId: string) => {
      const result = await connectConnector(connectorId);
      authorizeOauth(result.auth_request.authorization_endpoint, handleAuthorizeCallback);
    },
    [connectConnector, handleAuthorizeCallback],
  );
};

export const useAuthorize = () => {
  const handleAuthorizeCallback = useHandleAuthorizeCallback();

  return useCallback(
    (authorizationEndpoint: string) => {
      authorizeOauth(authorizationEndpoint, handleAuthorizeCallback);
    },
    [handleAuthorizeCallback],
  );
};
