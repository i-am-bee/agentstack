/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from '#api/index.ts';
import type { ContextPermissionsGrant, GlobalPermissionGrant } from '#api/types.ts';
import { ensureData } from '#api/utils.ts';

export async function createContext() {
  const response = await api.POST('/api/v1/contexts');

  return ensureData(response);
}

export async function matchProviders(suggestedModels: string[]) {
  const response = await api.POST('/api/v1/model_providers/match', {
    body: {
      capability: 'llm',
      score_cutoff: 0.4,
      suggested_models: suggestedModels,
    },
  });

  return ensureData(response);
}

export async function createContextToken(
  contextId: string,
  globalPermissionGrant: GlobalPermissionGrant,
  contextPermissionGrant: ContextPermissionsGrant,
) {
  const response = await api.POST('/api/v1/contexts/{context_id}/token', {
    body: {
      grant_context_permissions: contextPermissionGrant,
      grant_global_permissions: globalPermissionGrant,
    },
    params: {
      path: {
        context_id: contextId,
      },
    },
  });

  return ensureData(response);
}
