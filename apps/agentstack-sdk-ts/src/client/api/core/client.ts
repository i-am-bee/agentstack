/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import { createConfigurationApi } from '../configuration/api';
import { createConnectorsApi } from '../connectors/api';
import { createContextsApi } from '../contexts/api';
import { createFilesApi } from '../files/api';
import { createModelProvidersApi } from '../model-providers/api';
import { createProviderBuildsApi } from '../provider-builds/api';
import { createProvidersApi } from '../providers/api';
import { createUserFeedbackApi } from '../user-feedback/api';
import { createUsersApi } from '../users/api';
import { createVariablesApi } from '../variables/api';
import type { HttpError, NetworkError, ParseError, ValidationError } from './errors';
import { ApiErrorException, ApiErrorType } from './errors';
import type { ApiFailure, ApiRequest, ApiResult, CallApi } from './types';
import { buildRequestInit, buildRequestUrl, parseBodyText, safeReadText } from './utils';

function createCallApi({ baseUrl, fetch: fetchFn }: { baseUrl: string; fetch: typeof globalThis.fetch }): CallApi {
  return async function callApi({ method, path, schema, query, body, parseAsStream }) {
    const requestUrl = buildRequestUrl({ baseUrl, path, query });
    const requestInit = buildRequestInit({ method, body });

    const request: ApiRequest = {
      method,
      url: requestUrl,
    };

    try {
      const rawResponse = await fetchFn(requestUrl, requestInit);
      const bodyText = parseAsStream ? rawResponse.body : await safeReadText(rawResponse);

      const { ok, status, statusText, headers } = rawResponse;
      const response = { status, statusText, bodyText };

      if (!ok) {
        return {
          ok: false,
          error: {
            type: ApiErrorType.Http,
            message: 'API Http Error',
            request,
            response,
          } satisfies HttpError,
        } satisfies ApiFailure;
      }

      const { data: parsedBody, error: parseError } = parseBodyText(bodyText, headers);

      if (parseError) {
        return {
          ok: false,
          error: {
            type: ApiErrorType.Parse,
            message: 'API Parse Error',
            request,
            response,
            details: parseError,
          } satisfies ParseError,
        } satisfies ApiFailure;
      }

      const { data: result, success, error } = schema.safeParse(parsedBody);

      if (!success) {
        return {
          ok: false,
          error: {
            type: ApiErrorType.Validation,
            message: 'API Validation Error',
            request,
            response,
            details: error,
          } satisfies ValidationError,
        } satisfies ApiFailure;
      }

      return {
        ok: true,
        data: result,
        response,
      };
    } catch (details) {
      return {
        ok: false,
        error: {
          type: ApiErrorType.Network,
          message: 'API Network Error',
          request,
          details,
        } satisfies NetworkError,
      } satisfies ApiFailure;
    }
  };
}

export const buildApiClient = (
  {
    baseUrl,
    fetch: fetchFn,
  }: {
    baseUrl: string;
    fetch?: typeof globalThis.fetch;
  } = { baseUrl: '' },
) => {
  const maybeFetch = fetchFn ?? (typeof globalThis.fetch !== 'undefined' ? globalThis.fetch : undefined);

  if (!maybeFetch) {
    throw new Error(
      'fetch is not available. In Node.js < 18 or environments without global fetch, provide a fetch implementation via the fetch option.',
    );
  }

  const callApi = createCallApi({ baseUrl, fetch: maybeFetch });

  const configurationApi = createConfigurationApi(callApi);
  const connectorsApi = createConnectorsApi(callApi);
  const contextsApi = createContextsApi(callApi);
  const filesApi = createFilesApi(callApi);
  const modelProvidersApi = createModelProvidersApi(callApi);
  const providerBuildsApi = createProviderBuildsApi(callApi);
  const providersApi = createProvidersApi(callApi);
  const userFeedbackApi = createUserFeedbackApi(callApi);
  const usersApi = createUsersApi(callApi);
  const variablesApi = createVariablesApi(callApi);

  return {
    ...configurationApi,
    ...connectorsApi,
    ...contextsApi,
    ...filesApi,
    ...modelProvidersApi,
    ...providerBuildsApi,
    ...providersApi,
    ...userFeedbackApi,
    ...usersApi,
    ...variablesApi,
  };
};

export function unwrapResult<T>(result: ApiResult<T>): T;
export function unwrapResult<T, Out extends T>(result: ApiResult<T>, schema: z.ZodType<Out>): Out;
export function unwrapResult<T, Out extends T>(result: ApiResult<T>, schema?: z.ZodType<Out>): T | Out {
  if (result.ok) {
    const { data } = result;

    return schema ? schema.parse(data) : data;
  }

  throw new ApiErrorException(result.error);
}
