/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { createAuthenticatedFetch, getAgentCardPath } from 'agentstack-sdk';

import { UnauthenticatedError } from '#api/errors.ts';
import { getBaseUrl } from '#utils/api/getBaseUrl.ts';

import { type A2AClient, createA2AClient, fetchAgentCard } from './jsonrpc-client';

export async function getAgentClient(providerId: string, token: string): Promise<A2AClient> {
  const fetchImpl = createAuthenticatedFetch(token, clientFetch);

  const baseUrl = getBaseUrl();
  const agentCardUrl = `${baseUrl}/${getAgentCardPath(providerId)}`;
  const endpointUrl = `${baseUrl}/api/v1/a2a/${providerId}/`;

  const agentCard = await fetchAgentCard(agentCardUrl, fetchImpl);

  return createA2AClient({ endpointUrl, agentCard, fetchImpl });
}

async function clientFetch(input: RequestInfo, init?: RequestInit) {
  const response = await fetch(input, init);

  if (!response.ok && response.status === 401) {
    throw new UnauthenticatedError({ message: 'You are not authenticated.', response });
  }

  return response;
}
