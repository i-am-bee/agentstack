/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { providers } from '../../../../(auth)/auth';
import { getTokenEndpoint } from '../../../../(auth)/token-endpoint';

export async function POST(req: Request, { params }: { params: Promise<{ providerId: string }> }) {
  const body = await req.text();
  const postData = new URLSearchParams(body);

  const { providerId } = await params;
  const provider = providers.find(({ id }) => id === providerId);

  if (!provider || !provider.options) {
    throw new Error(`Provider with id '${providerId}' not found`);
  }

  const { clientId, clientSecret, issuer: issuerUrl } = provider.options;

  if (!clientId || !clientSecret || !issuerUrl) {
    throw new Error(`Provider is missing clientId, clientSecret, or issuer`);
  }

  const tokenUrl = await getTokenEndpoint(issuerUrl, clientId, clientSecret);

  postData.set('client_id', clientId);
  postData.set('client_secret', clientSecret);

  const res = await fetch(tokenUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: postData,
  });

  const data = await res.json();

  // Normalize token_type for NextAuth/oauth4webapi
  data.token_type = 'Bearer';

  return Response.json(data);
}
