/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export function createAuthenticatedFetch(
  token: string,
  baseFetch?: typeof fetch,
): typeof fetch {
  const fetchImpl = baseFetch ?? (typeof globalThis.fetch !== 'undefined' ? globalThis.fetch : undefined);

  if (!fetchImpl) {
    throw new Error(
      'fetch is not available. In Node.js < 18 or environments without global fetch, ' +
        'provide a fetch implementation via the baseFetch parameter.',
    );
  }

  return async (input: RequestInfo | URL, init?: RequestInit) => {
    const headers = new Headers(init?.headers);
    headers.set('Authorization', `Bearer ${token}`);
    return fetchImpl(input, { ...init, headers });
  };
}
