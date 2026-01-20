/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';
import type { TaskStatusUpdateEvent } from 'agentstack-sdk';

import { buildA2AClient } from '#api/a2a/client.ts';

import { runKeys } from '../keys';

type Props<UIGenericPart> = {
  providerId?: string;
  authToken?: string;
  onStatusUpdate?: (event: TaskStatusUpdateEvent) => UIGenericPart[];
};

export function useBuildA2AClient<UIGenericPart = never>({
  providerId = '',
  authToken = '',
  onStatusUpdate,
}: Props<UIGenericPart>) {
  const { data: agentClient } = useQuery({
    queryKey: runKeys.client(providerId),
    queryFn: async () =>
      buildA2AClient<UIGenericPart>({
        providerId,
        authToken,
        onStatusUpdate,
      }),
    enabled: Boolean(providerId && authToken),
    staleTime: Infinity,
  });

  return { agentClient };
}
