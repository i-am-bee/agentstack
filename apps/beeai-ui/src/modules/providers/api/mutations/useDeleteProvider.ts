/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import { agentKeys } from '#modules/agents/api/keys.ts';
import type { Agent } from '#modules/agents/api/types.ts';
import { providerKeys } from '#modules/providers/api/keys.ts';

import { deleteProvider } from '..';

export function useDeleteProvider() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: deleteProvider,
    onSuccess: (_data, variables) => {
      // The removal of the provider agents is basically done immediately, but it is an asynchronous operation, so instead of the classic invalidation that would return the old data, we set the correct data here.
      queryClient.setQueriesData<{ agents: Agent[] }>(
        {
          queryKey: agentKeys.lists(),
        },
        (data) => {
          const agents = data?.agents.filter((agent) => agent.metadata.provider !== variables.id);

          return agents
            ? {
                ...data,
                agents,
              }
            : data;
        },
      );
    },
    meta: {
      invalidates: [providerKeys.lists()],
      errorToast: {
        title: 'Failed to delete provider.',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
