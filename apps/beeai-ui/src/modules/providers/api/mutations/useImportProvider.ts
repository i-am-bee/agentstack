/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';

import { StreamError } from '#api/errors.ts';
import { handleStream } from '#api/utils.ts';
import { agentKeys } from '#modules/agents/api/keys.ts';
import { useMonitorProviderStatus } from '#modules/providers/hooks/useMonitorProviderStatus.ts';

import { registerManagedProvider } from '..';
import { providerKeys } from '../keys';
import { useProviderBySource } from '../queries/useProviderBySource';
import type { Provider, ProviderImportEvent, ProviderLocation, RegisterProviderRequest } from '../types';

interface Props {
  onSuccess?: (data?: Provider) => void;
}

export function useImportProvider({ onSuccess }: Props = {}) {
  const [id, setId] = useState<string>();
  const [location, setLocation] = useState<ProviderLocation>();
  const { refetch } = useProviderBySource({ source: location });

  useMonitorProviderStatus({ id });

  const mutation = useMutation({
    mutationFn: async ({ body }: { body: RegisterProviderRequest }) => {
      setLocation(body.location);

      const stream = await registerManagedProvider({ body });

      await handleStream<ProviderImportEvent>({
        stream,
        onEvent: (event) => {
          if ('error' in event) {
            throw new StreamError({ error: event.error });
          }
        },
      });

      const { data: provider } = await refetch();

      if (provider) {
        setId(provider.id);
      }

      return provider;
    },
    onSuccess,
    meta: {
      invalidates: [providerKeys.lists(), agentKeys.lists()],
      errorToast: {
        title: 'Failed to import provider.',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
