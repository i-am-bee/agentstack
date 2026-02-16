/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {
  ClientFactory,
  ClientFactoryOptions,
  DefaultAgentCardResolver,
  JsonRpcTransportFactory,
} from '@a2a-js/sdk/client';
import { createAuthenticatedFetch, getAgentCardPath } from 'agentstack-sdk';

import { UnauthenticatedError } from '#api/errors.ts';
import { getBaseUrl } from '#utils/api/getBaseUrl.ts';

export async function getAgentClient(providerId: string, token: string) {
  const fetchImpl = createAuthenticatedFetch(token, clientFetch);

  const baseUrl = getBaseUrl();
  const agentCardPath = getAgentCardPath(providerId);
  const factory = new ClientFactory(
    ClientFactoryOptions.createFrom(ClientFactoryOptions.default, {
      transports: [new JsonRpcTransportFactory({ fetchImpl })],
      cardResolver: new DefaultAgentCardResolver({ fetchImpl }),
    }),
  );
  const client = await factory.createFromUrl(baseUrl, agentCardPath);

  return client;
}

async function clientFetch(input: RequestInfo, init?: RequestInit) {
  const response = await fetch(input, init);

  if (!response.ok && response.status === 401) {
    throw new UnauthenticatedError({ message: 'You are not authenticated.', response });
  }

  return response;
}
