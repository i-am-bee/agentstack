/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import { GitHubVersionType } from './types';

export const gitHubVersionTypeSchema = z.enum(GitHubVersionType);

export const gitHubRegistryLocationSchema = z.string();

export const networkRegistryLocationSchema = z.string();

export const fileSystemRegistryLocationSchema = z.string();

export const dockerImageIdSchema = z.string();

export const dockerImageProviderLocationSchema = dockerImageIdSchema;

export const networkProviderLocationSchema = z.string();

export const resolvedGitHubUrlSchema = z.object({
  host: z.string(),
  org: z.string(),
  repo: z.string(),
  version: z.string(),
  version_type: gitHubVersionTypeSchema,
  commit_hash: z.string(),
  path: z.string().nullish(),
});

export const resolvedDockerImageIdSchema = z.object({
  registry: z.string(),
  repository: z.string(),
  tag: z.string(),
  digest: z.string(),
  image_id: dockerImageIdSchema,
});

export const readableStreamSchema = z.custom<ReadableStream<Uint8Array<ArrayBuffer>>>(
  (value) => value instanceof ReadableStream,
  { error: 'Expected ReadableStream' },
);
