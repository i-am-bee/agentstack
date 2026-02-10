/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { buildApiClient, unwrapResult } from 'agentstack-sdk';

import { BASE_URL, PROVIDER_ID } from './constants';

export const api = buildApiClient({ baseUrl: BASE_URL });

export async function createContext() {
  const result = await api.createContext({ provider_id: PROVIDER_ID });

  return unwrapResult(result);
}

export async function createContextToken(contextId: string) {
  const result = await api.createContextToken({
    context_id: contextId,
    grant_global_permissions: {
      a2a_proxy: [PROVIDER_ID],
      llm: ['*'],
    },
    grant_context_permissions: {
      context_data: ['*'],
    },
  });

  return unwrapResult(result);
}
