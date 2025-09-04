/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ServerSentEventMessage } from 'fetch-event-stream';
import type { FetchResponse } from 'openapi-fetch';
import type { MediaType } from 'openapi-typescript-helpers';

import { isNotNull } from '#utils/helpers.ts';

import { AcpError, ApiError, ApiValidationError, HttpError } from './errors';
import type { AcpErrorResponse, ApiErrorCode, ApiErrorResponse, ApiValidationErrorResponse } from './types';

export function ensureData<T extends Record<string | number, unknown>, O, M extends MediaType>(
  response: FetchResponse<T, O, M>,
) {
  if ('error' in response) {
    handleFailedError({ response: response.response, error: response.error });
  }

  return response.data;
}

function handleFailedError({ response, error }: { response: Response; error: unknown }) {
  if (typeof error === 'object' && isNotNull(error)) {
    if ('detail' in error) {
      const { detail } = error;

      if (typeof detail === 'object') {
        throw new ApiValidationError({ error: error as ApiValidationErrorResponse, response });
      } else if (typeof detail === 'string') {
        throw new HttpError({ message: detail, response });
      }

      throw new HttpError({ message: 'An error occurred', response });
    } else if ('error' in error) {
      throw new AcpError({ error: error as AcpErrorResponse, response });
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
