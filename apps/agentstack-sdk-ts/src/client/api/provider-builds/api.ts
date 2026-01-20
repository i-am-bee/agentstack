/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { CallApi } from '../core/types';
import { ApiMethod } from '../core/types';
import {
  createProviderBuildResponseSchema,
  deleteProviderBuildResponseSchema,
  listProviderBuildsResponseSchema,
  previewProviderBuildResponseSchema,
  readProviderBuildLogsResponseSchema,
  readProviderBuildResponseSchema,
} from './schemas';
import type {
  CreateProviderBuildRequest,
  DeleteProviderBuildRequest,
  ListProviderBuildsRequest,
  PreviewProviderBuildRequest,
  ReadProviderBuildLogsRequest,
  ReadProviderBuildRequest,
} from './types';

export function createProviderBuildsApi(callApi: CallApi) {
  const listProviderBuilds = ({ query }: ListProviderBuildsRequest) =>
    callApi({
      method: ApiMethod.Get,
      path: '/api/v1/provider_builds',
      schema: listProviderBuildsResponseSchema,
      query,
    });

  const createProviderBuild = ({ ...body }: CreateProviderBuildRequest) =>
    callApi({
      method: ApiMethod.Post,
      path: '/api/v1/provider_builds',
      schema: createProviderBuildResponseSchema,
      body,
    });

  const readProviderBuild = ({ id }: ReadProviderBuildRequest) =>
    callApi({
      method: ApiMethod.Get,
      path: `/api/v1/provider_builds/${id}`,
      schema: readProviderBuildResponseSchema,
    });

  const deleteProviderBuild = ({ id }: DeleteProviderBuildRequest) =>
    callApi({
      method: ApiMethod.Delete,
      path: `/api/v1/provider_builds/${id}`,
      schema: deleteProviderBuildResponseSchema,
    });

  const readProviderBuildLogs = ({ id }: ReadProviderBuildLogsRequest) =>
    callApi({
      method: ApiMethod.Get,
      path: `/api/v1/provider_builds/${id}/logs`,
      schema: readProviderBuildLogsResponseSchema,
      parseAsStream: true,
    });

  const previewProviderBuild = ({ ...body }: PreviewProviderBuildRequest) =>
    callApi({
      method: ApiMethod.Post,
      path: '/api/v1/provider_builds/preview',
      schema: previewProviderBuildResponseSchema,
      body,
    });

  return {
    listProviderBuilds,
    createProviderBuild,
    readProviderBuild,
    deleteProviderBuild,
    readProviderBuildLogs,
    previewProviderBuild,
  };
}
