/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { redirect } from 'next/navigation';
import type { NextRequest } from 'next/server';

import { ensureToken } from '#app/(auth)/rsc.tsx';
import { runtimeConfig } from '#contexts/App/runtime-config.ts';
import { API_URL } from '#utils/constants.ts';
import { routes } from '#utils/router.ts';

import { transformAgentManifestBody } from './body-transformers';
import { isApiAgentManifestUrl, isUrlTrailingSlashNeeded } from './utils';

type RouteContext = {
  params: Promise<{
    path: string[];
  }>;
};

async function handler(request: NextRequest, context: RouteContext) {
  const { method, headers, body, nextUrl } = request;
  const { path } = await context.params;
  const search = nextUrl.search;
  const url = new URL(API_URL);
  let targetUrl = `${url}api/${path.join('/')}`;
  // Ensure that URLs that need a trailing slash get one, because Next.js removes it for all routes
  if (isUrlTrailingSlashNeeded(targetUrl)) {
    targetUrl += '/';
  }
  targetUrl += search;

  if (runtimeConfig.isAuthEnabled) {
    const token = await ensureToken(request);

    if (!token) {
      redirect(routes.signIn());
    }

    if (token?.access_token) {
      headers.set('Authorization', `Bearer ${token.access_token}`);
    }
  }

  if (!headers.has('Forwarded')) {
    headers.set('Forwarded', `host=${nextUrl.host};proto=${nextUrl.protocol.replace(/:$/, '')}`);
  }

  const forwarded_header = headers.get('forwarded');
  const forwarded_host = nextUrl.host;
  const forwarded_proto = nextUrl.protocol.replace(/:$/, '');
  headers.set(
    'forwarded',
    [...(forwarded_header ? [forwarded_header] : []), `host=${forwarded_host};proto=${forwarded_proto}`].join(','),
  );
  headers.set('x-forwarded-host', forwarded_host);
  headers.set('x-forwarded-proto', forwarded_proto);

  const res = await fetch(targetUrl, {
    method,
    headers,
    body,
    // @ts-expect-error - TS does not know `duplex`, but it's required by some
    // browsers for stream requests https://fetch.spec.whatwg.org/#ref-for-dom-requestinit-duplex
    duplex: body ? 'half' : undefined,
  });

  let responseBody: ReadableStream<Uint8Array<ArrayBufferLike>> | string | null = res.body;
  if (isApiAgentManifestUrl(targetUrl)) {
    responseBody = await transformAgentManifestBody(res);
  }

  return new Response(responseBody, {
    status: res.status,
    headers: {
      'Content-Type': res.headers.get('Content-Type') || 'text/plain',
    },
  });
}

export { handler as DELETE, handler as GET, handler as PATCH, handler as POST, handler as PUT };
