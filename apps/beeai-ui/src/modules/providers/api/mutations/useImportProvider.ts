/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';

import { StreamError } from '#api/errors.ts';
import { handleStream } from '#api/utils.ts';
import { agentKeys } from '#modules/agents/api/keys.ts';
import type { AgentProvider } from '#modules/agents/api/types.ts';
import { useMonitorProvider } from '#modules/providers/hooks/useMonitorProviderStatus.ts';

import { registerManagedProvider } from '..';
import { providerKeys } from '../keys';
import { useProvider } from '../queries/useProvider';
import type { Provider, ProviderImportEvent, ProviderLocation, RegisterManagedProviderRequest } from '../types';

interface Props {
  onSuccess?: (data?: Provider) => void;
}

export function useImportProvider({ onSuccess }: Props = {}) {
  const [id, setId] = useState<AgentProvider>();
  const [location, setLocation] = useState<ProviderLocation>();
  const { refetch } = useProvider({ id: location });

  useMonitorProvider({ id });

  const mutation = useMutation({
    mutationFn: async ({ body }: { body: RegisterManagedProviderRequest }) => {
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
