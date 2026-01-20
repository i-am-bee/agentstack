/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { CallApi } from '../core/types';
import { ApiMethod } from '../core/types';
import {
  createContextHistoryResponseSchema,
  createContextResponseSchema,
  createContextTokenResponseSchema,
  deleteContextResponseSchema,
  listContextHistoryResponseSchema,
  listContextsResponseSchema,
  patchContextMetadataResponseSchema,
  readContextResponseSchema,
  updateContextResponseSchema,
} from './schemas';
import type {
  CreateContextHistoryRequest,
  CreateContextRequest,
  CreateContextTokenRequest,
  DeleteContextRequest,
  ListContextHistoryRequest,
  ListContextsRequest,
  PatchContextMetadataRequest,
  ReadContextRequest,
  UpdateContextRequest,
} from './types';

export function createContextsApi(callApi: CallApi) {
  const listContexts = ({ query }: ListContextsRequest) =>
    callApi({
      method: ApiMethod.Get,
      path: '/api/v1/contexts',
      schema: listContextsResponseSchema,
      query,
    });

  const createContext = ({ ...body }: CreateContextRequest) =>
    callApi({
      method: ApiMethod.Post,
      path: '/api/v1/contexts',
      schema: createContextResponseSchema,
      body,
    });

  const readContext = ({ context_id }: ReadContextRequest) =>
    callApi({
      method: ApiMethod.Get,
      path: `/api/v1/contexts/${context_id}`,
      schema: readContextResponseSchema,
    });

  const updateContext = ({ context_id, ...body }: UpdateContextRequest) =>
    callApi({
      method: ApiMethod.Put,
      path: `/api/v1/contexts/${context_id}`,
      schema: updateContextResponseSchema,
      body,
    });

  const deleteContext = ({ context_id }: DeleteContextRequest) =>
    callApi({
      method: ApiMethod.Delete,
      path: `/api/v1/contexts/${context_id}`,
      schema: deleteContextResponseSchema,
    });

  const listContextHistory = ({ context_id, query }: ListContextHistoryRequest) =>
    callApi({
      method: ApiMethod.Get,
      path: `/api/v1/contexts/${context_id}/history`,
      schema: listContextHistoryResponseSchema,
      query,
    });

  const createContextHistory = ({ context_id, ...body }: CreateContextHistoryRequest) =>
    callApi({
      method: ApiMethod.Post,
      path: `/api/v1/contexts/${context_id}/history`,
      schema: createContextHistoryResponseSchema,
      body,
    });

  const patchContextMetadata = ({ context_id, ...body }: PatchContextMetadataRequest) =>
    callApi({
      method: ApiMethod.Patch,
      path: `/api/v1/contexts/${context_id}/metadata`,
      schema: patchContextMetadataResponseSchema,
      body,
    });

  const createContextToken = ({ context_id, ...body }: CreateContextTokenRequest) =>
    callApi({
      method: ApiMethod.Post,
      path: `/api/v1/contexts/${context_id}/token`,
      schema: createContextTokenResponseSchema,
      body,
    });

  return {
    listContexts,
    createContext,
    readContext,
    updateContext,
    deleteContext,
    listContextHistory,
    createContextHistory,
    patchContextMetadata,
    createContextToken,
  };
}
