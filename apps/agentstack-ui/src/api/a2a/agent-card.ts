/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { A2AClient } from '@a2a-js/sdk/client';
import { createAuthenticatedFetch } from 'agentstack-sdk';

import { UnauthenticatedError } from '#api/errors.ts';
import { getBaseUrl } from '#utils/api/getBaseUrl.ts';

export async function getAgentClient(providerId: string, token?: string) {
  const agentCardUrl = `${getBaseUrl()}/api/v1/a2a/${providerId}/.well-known/agent-card.json`;

  const fetchImpl = token ? createAuthenticatedFetch(token, clientFetch) : clientFetch;
  return await A2AClient.fromCardUrl(agentCardUrl, { fetchImpl });
}

export async function clientFetch(input: RequestInfo, init?: RequestInit) {
  const response = await fetch(input, init);
  if (!response.ok && response.status === 401) {
    throw new UnauthenticatedError({ message: 'You are not authenticated.', response });
  }

  return response;
}
