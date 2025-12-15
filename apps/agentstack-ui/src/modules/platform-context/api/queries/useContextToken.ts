/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';
import type { ContextToken } from 'agentstack-sdk';

import { useApp } from '#contexts/App/index.ts';
import type { Agent } from '#modules/agents/api/types.ts';

import { usePlatformContext } from '../../contexts';
import { createContextToken } from '..';
import { contextKeys } from '../keys';

export function useContextToken(agent: Agent) {
  const {
    config: { contextTokenPermissions },
  } = useApp();
  const { contextId } = usePlatformContext();

  return useQuery<ContextToken>({
    queryKey: contextKeys.token(contextId ?? '', agent.provider.id),
    queryFn: async () => {
      if (!contextId) {
        throw new Error('Context ID is not set.');
      }

      const token = await createContextToken({
        context_id: contextId,
        grant_context_permissions: contextTokenPermissions.grant_context_permissions ?? {},
        grant_global_permissions: contextTokenPermissions.grant_global_permissions ?? {},
      });

      if (!token) {
        throw new Error('Could not generate context token');
      }

      return token;
    },
    enabled: !!contextId,
    staleTime: Infinity,
  });
}
