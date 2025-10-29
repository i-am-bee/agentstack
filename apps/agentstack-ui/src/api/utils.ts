/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentExtension as A2AAgentExtension } from '@a2a-js/sdk';
import type { ServerSentEventMessage } from 'fetch-event-stream';
import type { FetchResponse } from 'openapi-fetch';
import type { MediaType } from 'openapi-typescript-helpers';

import type { Agent } from '#modules/agents/api/types.ts';
import { NEXTAUTH_URL, TRUST_PROXY_HEADERS } from '#utils/constants.ts';
import { isNotNull } from '#utils/helpers.ts';

import { ApiError, ApiValidationError, HttpError, UnauthenticatedError } from './errors';
import type { ApiErrorCode, ApiErrorResponse, ApiValidationErrorResponse } from './types';

export function ensureData<T extends Record<string | number, unknown>, O, M extends MediaType>(
  fetchResponse: FetchResponse<T, O, M>,
) {
  const { response, data, error } = fetchResponse;

  if (response.status === 401) {
    throw new UnauthenticatedError({ message: 'You are not authenticated.', response });
  }

  if (error) {
    handleFailedResponse({ response, error });
  }

  return data;
}

function handleFailedResponse({ response, error }: { response: Response; error: unknown }) {
  if (typeof error === 'object' && isNotNull(error)) {
    if ('detail' in error) {
      const { detail } = error;

      if (typeof detail === 'object') {
        throw new ApiValidationError({ error: error as ApiValidationErrorResponse, response });
      } else if (typeof detail === 'string') {
        throw new HttpError({ message: detail, response });
      }

      throw new HttpError({ message: 'An error occurred', response });
    }

    throw new ApiError({ error: error as ApiErrorResponse, response });
  }

  throw new HttpError({ message: 'An error occurred.', response });
}

export async function handleStream<T>({
  stream,
  onEvent,
}: {
  stream: AsyncGenerator<ServerSentEventMessage>;
  onEvent?: (event: T) => void;
}): Promise<void> {
  for await (const event of stream) {
    if (event.data) {
      onEvent?.(JSON.parse(event.data));
    }
  }
}

export function getErrorMessage(error: unknown) {
  return typeof error === 'object' && isNotNull(error) && 'message' in error ? (error.message as string) : undefined;
}

export function getErrorCode(error: unknown) {
  return typeof error === 'object' && isNotNull(error) && 'code' in error
    ? (error.code as number | ApiErrorCode)
    : undefined;
}

export async function fetchEntity<T>(fetchFn: () => Promise<T>): Promise<T | undefined> {
  try {
    return await fetchFn();
  } catch (error) {
    console.error(error);

    return undefined;
  }
}

export function getAgentExtensions(agent?: Agent): A2AAgentExtension[] {
  const extensions = agent?.capabilities.extensions;
  if (!extensions) {
    return [];
  }

  return extensions.map(({ description, params, required, ...rest }) => ({
    ...rest,
    description: description ?? undefined,
    params: params ?? undefined,
    required: required ?? undefined,
  }));
}

export async function getProxyHeaders(headers: Headers, url?: URL) {
  const forwardedHost = (TRUST_PROXY_HEADERS && headers.get('x-forwarded-host')) || url?.host || NEXTAUTH_URL?.host;
  const forwardedProto =
    (TRUST_PROXY_HEADERS && headers.get('x-forwarded-proto')) ||
    (url?.protocol ?? NEXTAUTH_URL?.protocol)?.replace(/:$/, '');
  const forwarded = [
    ...(TRUST_PROXY_HEADERS ? [headers.get('forwarded') ?? `host=${forwardedHost};proto=${forwardedProto}`] : []),
    `host=${forwardedHost};proto=${forwardedProto}`,
  ].join(',');

  return { forwardedHost, forwardedProto, forwarded };
}
