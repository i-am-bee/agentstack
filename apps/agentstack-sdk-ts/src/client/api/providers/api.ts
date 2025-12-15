/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { CallApi } from '../core/types';
import { ApiMethod } from '../core/types';
import {
  createProviderResponseSchema,
  deleteProviderResponseSchema,
  listProvidersResponseSchema,
  listProviderVariablesResponseSchema,
  patchProviderResponseSchema,
  previewProviderResponseSchema,
  readProviderByLocationResponseSchema,
  readProviderLogsResponseSchema,
  readProviderResponseSchema,
  updateProviderVariablesResponseSchema,
} from './schemas';
import type {
  CreateProviderRequest,
  DeleteProviderRequest,
  ListProvidersRequest,
  ListProviderVariablesRequest,
  PatchProviderRequest,
  PreviewProviderRequest,
  ReadProviderByLocationRequest,
  ReadProviderLogsRequest,
  ReadProviderRequest,
  UpdateProviderVariablesRequest,
} from './types';

export function createProvidersApi(callApi: CallApi) {
  const listProviders = ({ query }: ListProvidersRequest) =>
    callApi({
      method: ApiMethod.Get,
      path: '/api/v1/providers',
      schema: listProvidersResponseSchema,
      query,
    });

  const createProvider = ({ ...body }: CreateProviderRequest) =>
    callApi({
      method: ApiMethod.Post,
      path: '/api/v1/providers',
      schema: createProviderResponseSchema,
      body,
    });

  const readProvider = ({ id }: ReadProviderRequest) =>
    callApi({
      method: ApiMethod.Get,
      path: `/api/v1/providers/${id}`,
      schema: readProviderResponseSchema,
    });

  const deleteProvider = ({ id }: DeleteProviderRequest) =>
    callApi({
      method: ApiMethod.Delete,
      path: `/api/v1/providers/${id}`,
      schema: deleteProviderResponseSchema,
    });

  const patchProvider = ({ id, ...body }: PatchProviderRequest) =>
    callApi({
      method: ApiMethod.Patch,
      path: `/api/v1/providers/${id}`,
      schema: patchProviderResponseSchema,
      body,
    });

  const readProviderLogs = ({ id }: ReadProviderLogsRequest) =>
    callApi({
      method: ApiMethod.Get,
      path: `/api/v1/providers/${id}/logs`,
      schema: readProviderLogsResponseSchema,
      parseAsStream: true,
    });

  const listProviderVariables = ({ id }: ListProviderVariablesRequest) =>
    callApi({
      method: ApiMethod.Get,
      path: `/api/v1/providers/${id}/variables`,
      schema: listProviderVariablesResponseSchema,
    });

  const updateProviderVariables = ({ id, ...body }: UpdateProviderVariablesRequest) =>
    callApi({
      method: ApiMethod.Put,
      path: `/api/v1/providers/${id}/variables`,
      schema: updateProviderVariablesResponseSchema,
      body,
    });

  const readProviderByLocation = ({ location }: ReadProviderByLocationRequest) =>
    callApi({
      method: ApiMethod.Get,
      path: `/api/v1/providers/by-location/${location}`,
      schema: readProviderByLocationResponseSchema,
    });

  const previewProvider = ({ ...body }: PreviewProviderRequest) =>
    callApi({
      method: ApiMethod.Post,
      path: '/api/v1/providers/preview',
      schema: previewProviderResponseSchema,
      body,
    });

  return {
    listProviders,
    createProvider,
    readProvider,
    deleteProvider,
    patchProvider,
    readProviderLogs,
    listProviderVariables,
    updateProviderVariables,
    readProviderByLocation,
    previewProvider,
  };
}
