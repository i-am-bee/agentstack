/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { CreateProviderBuildRequest, PreviewProviderBuildRequest, ReadProviderBuildRequest } from 'agentstack-sdk';
import { unwrapResult } from 'agentstack-sdk';

import { agentStackClient } from '#api/agentstack-client.ts';

export async function createProviderBuild(request: CreateProviderBuildRequest) {
  const response = await agentStackClient.createProviderBuild(request);
  const result = unwrapResult(response);

  return result;
}

export async function readProviderBuild(request: ReadProviderBuildRequest) {
  const response = await agentStackClient.readProviderBuild(request);
  const result = unwrapResult(response);

  return result;
}

export async function readProviderBuildLogs(request: ReadProviderBuildRequest) {
  const response = await agentStackClient.readProviderBuildLogs(request);
  const result = unwrapResult(response);

  return result;
}

export async function previewProviderBuild(request: PreviewProviderBuildRequest) {
  const response = await agentStackClient.previewProviderBuild(request);
  const result = unwrapResult(response);

  return result;
}
