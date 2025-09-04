/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { buildA2AClient, type CreateA2AClientParams } from '#api/a2a/client.ts';

type Props<UIGenericPart> = Omit<CreateA2AClientParams<UIGenericPart>, 'providerId'> & {
  providerId?: string;
};

export function useBuildA2AClient<UIGenericPart = never>({
  providerId,
  extensions,
  onStatusUpdate,
}: Props<UIGenericPart>) {
  const { data: agentClient } = useQuery({
    queryKey: ['agent', 'client', providerId],
    queryFn: async () =>
      providerId
        ? buildA2AClient<UIGenericPart>({
            providerId,
            extensions,
            onStatusUpdate,
          })
        : undefined,
    staleTime: Infinity,
  });

  return { agentClient };
}
