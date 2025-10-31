import { useCallback } from 'react';
import { useDeleteConnector } from '../api/mutations/useDeleteConnector';
import { useDisconnectConnector } from '../api/mutations/useDisconnectConnector';
import { useConnectConnector } from '../api/mutations/useConnectConnector';
import { useQueryClient } from '@tanstack/react-query';
import { connectorKeys } from '../api/keys';

const authorizeOauth = (url: string, onCallback: () => void) => {
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

  async function handler(_: unknown) {
    onCallback();

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

export const useConnect = () => {
  const queryClient = useQueryClient();
  const { mutateAsync: connectConnector } = useConnectConnector();

  return useCallback(
    async (connectorId: string) => {
      const result = await connectConnector(connectorId);

      authorizeOauth(result.auth_request.authorization_endpoint, () => {
        queryClient.invalidateQueries({ queryKey: connectorKeys.list() });
      });
    },
    [connectConnector, queryClient],
  );
};

export const useAuthorize = () => {
  const queryClient = useQueryClient();

  return useCallback(
    (authorizationEndpoint: string) => {
      authorizeOauth(authorizationEndpoint, () => {
        queryClient.invalidateQueries({ queryKey: connectorKeys.list() });
      });
    },
    [queryClient],
  );
};
