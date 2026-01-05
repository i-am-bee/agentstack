/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { buildA2AClient, type CreateA2AClientParams } from '#api/a2a/client.ts';

import { runKeys } from '../keys';

type Props<UIGenericPart> = Omit<CreateA2AClientParams<UIGenericPart>, 'providerId'> & {
  providerId?: string;
};

export function useBuildA2AClient<UIGenericPart = never>({
  providerId = '',
  onStatusUpdate,
  authToken,
}: Props<UIGenericPart>) {
  const { data: agentClient } = useQuery({
    queryKey: runKeys.client(`${providerId}${Boolean(authToken)}`),
    queryFn: async () =>
      buildA2AClient<UIGenericPart>({
        providerId,
        onStatusUpdate,
        authToken,
      }),
    enabled: Boolean(providerId),
    staleTime: Infinity,
  });

  return { agentClient };
}
