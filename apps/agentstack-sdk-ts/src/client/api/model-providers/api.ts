/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { CallApi } from '../core/types';
import { ApiMethod } from '../core/types';
import {
  createModelProviderResponseSchema,
  deleteModelProviderResponseSchema,
  listModelProvidersResponseSchema,
  matchModelProvidersResponseSchema,
  readModelProviderResponseSchema,
} from './schemas';
import type {
  CreateModelProviderRequest,
  DeleteModelProviderRequest,
  MatchModelProvidersRequest,
  ReadModelProviderRequest,
} from './types';

export function createModelProvidersApi(callApi: CallApi) {
  const listModelProviders = () =>
    callApi({
      method: ApiMethod.Get,
      path: '/api/v1/model_providers',
      schema: listModelProvidersResponseSchema,
    });

  const createModelProvider = ({ ...body }: CreateModelProviderRequest) =>
    callApi({
      method: ApiMethod.Post,
      path: '/api/v1/model_providers',
      schema: createModelProviderResponseSchema,
      body,
    });

  const readModelProvider = ({ model_provider_id }: ReadModelProviderRequest) =>
    callApi({
      method: ApiMethod.Get,
      path: `/api/v1/model_providers/${model_provider_id}`,
      schema: readModelProviderResponseSchema,
    });

  const deleteModelProvider = ({ model_provider_id }: DeleteModelProviderRequest) =>
    callApi({
      method: ApiMethod.Delete,
      path: `/api/v1/model_providers/${model_provider_id}`,
      schema: deleteModelProviderResponseSchema,
    });

  const matchModelProviders = ({ ...body }: MatchModelProvidersRequest) =>
    callApi({
      method: ApiMethod.Post,
      path: '/api/v1/model_providers/match',
      schema: matchModelProvidersResponseSchema,
      body,
    });

  return {
    listModelProviders,
    createModelProvider,
    readModelProvider,
    deleteModelProvider,
    matchModelProviders,
  };
}
