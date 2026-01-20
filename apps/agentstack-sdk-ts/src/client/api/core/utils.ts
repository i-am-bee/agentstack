/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ApiMethod, ApiQueryParams, ApiRequestBody } from './types';

export function buildRequestUrl({ baseUrl, path, query }: { baseUrl: string; path: string; query?: ApiQueryParams }) {
  const url = `${baseUrl.replace(/\/+$/, '')}${path}`;

  if (query) {
    const searchParams = new URLSearchParams();

    Object.entries(query).forEach(([key, value]) => {
      if (value != null) {
        searchParams.append(key, String(value));
      }
    });

    const queryString = searchParams.toString();

    if (queryString) {
      return `${url}?${queryString}`;
    }
  }

  return url;
}

export function buildRequestInit({ method, body }: { method: ApiMethod; body?: ApiRequestBody }) {
  const headers = new Headers();

  let requestBody: FormData | string | undefined;

  if (body) {
    if (body instanceof FormData) {
      requestBody = body;
    } else {
      headers.set('Content-Type', 'application/json');

      requestBody = JSON.stringify(body);
    }
  }

  return {
    method,
    headers,
    body: requestBody,
  };
}

export async function safeReadText(response: Response) {
  try {
    return await response.text();
  } catch {
    return null;
  }
}

export function parseBodyText(
  bodyText: ReadableStream<Uint8Array> | string | null,
  headers: Headers,
): {
  data: unknown;
  error?: Error;
} {
  const isStreamResponse = bodyText instanceof ReadableStream;

  if (isStreamResponse) {
    return {
      data: bodyText,
    };
  }

  if (bodyText == null || bodyText.trim() === '') {
    return {
      data: null,
    };
  }

  const contentType = headers.get('content-type') ?? '';
  const isJsonResponse = contentType.includes('application/json');

  if (isJsonResponse) {
    try {
      return {
        data: JSON.parse(bodyText),
      };
    } catch (error) {
      return {
        data: null,
        error: error instanceof Error ? error : new Error('Failed to parse body text.'),
      };
    }
  }

  return {
    data: bodyText,
  };
}
