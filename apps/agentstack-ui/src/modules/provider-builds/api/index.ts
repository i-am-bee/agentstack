/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from '#api/index.ts';
import { ensureData } from '#api/utils.ts';

import type {
  CreateProviderBuildRequest,
  PreviewProviderBuildRequest,
  ReadProviderBuildLogsPath,
  ReadProviderBuildPath,
} from './types';

export async function createProviderBuild(body: CreateProviderBuildRequest) {
  const response = await api.POST('/api/v1/provider_builds', { body });

  return ensureData(response);
}

export async function listProviderBuilds() {
  const response = await api.GET('/api/v1/provider_builds');

  return ensureData(response);
}

export async function previewProviderBuild(body: PreviewProviderBuildRequest) {
  const response = await api.POST('/api/v1/provider_builds/preview', { body });

  return ensureData(response);
}

export async function readProviderBuild(path: ReadProviderBuildPath) {
  const response = await api.GET('/api/v1/provider_builds/{id}', { params: { path } });

  return ensureData(response);
}

export async function readProviderBuildLogs(path: ReadProviderBuildLogsPath) {
  const response = await api.GET('/api/v1/provider_builds/{id}/logs', { parseAs: 'stream', params: { path } });

  return ensureData(response);
}
