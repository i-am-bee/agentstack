/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import { agentKeys } from '#modules/agents/api/keys.ts';
import { providerKeys } from '#modules/providers/api/keys.ts';

import { deleteProvider } from '..';
import type { ProvidersListResponse } from '../types';

export function useDeleteProvider() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: deleteProvider,
    onSuccess: (_data, variables) => {
      queryClient.setQueryData<ProvidersListResponse>(agentKeys.lists(), (data) => {
        if (!data) {
          return data;
        }

        const items = data?.items.filter(({ id }) => id !== variables.id) ?? [];

        return { ...data, items };
      });
    },
    meta: {
      invalidates: [providerKeys.lists(), agentKeys.lists()],
      errorToast: {
        title: 'Failed to delete provider.',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
