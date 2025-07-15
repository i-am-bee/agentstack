/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { NextRequest } from 'next/server';

type RouteContext = {
  params: Promise<{
    path: string[];
  }>;
};

async function handler(request: NextRequest, context: RouteContext) {
  const { method, headers, body, nextUrl } = request;
  const { path } = await context.params;
  const search = nextUrl.search;

  const url = new URL(process.env.API_URL!);
  const targetUrl = `${url}api/${path.join('/')}${search}`;

  const res = await fetch(targetUrl, {
    method,
    headers,
    body,
    // @ts-expect-error - TS does not know `duplex`, but it's required by some
    // browsers for stream requests https://fetch.spec.whatwg.org/#ref-for-dom-requestinit-duplex
    duplex: body ? 'half' : undefined,
  });

  return new Response(res.body, {
    status: res.status,
    headers: {
      'Content-Type': res.headers.get('Content-Type') || 'text/plain',
    },
  });
}

export { handler as DELETE, handler as GET, handler as PATCH, handler as POST, handler as PUT };
