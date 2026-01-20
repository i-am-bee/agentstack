/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type {
  dockerImageIdSchema,
  dockerImageProviderLocationSchema,
  fileSystemRegistryLocationSchema,
  gitHubRegistryLocationSchema,
  networkProviderLocationSchema,
  networkRegistryLocationSchema,
  resolvedDockerImageIdSchema,
  resolvedGitHubUrlSchema,
} from './schemas';

export enum GitHubVersionType {
  Head = 'head',
  Tag = 'tag',
}

export type GitHubRegistryLocation = z.infer<typeof gitHubRegistryLocationSchema>;
export type NetworkRegistryLocation = z.infer<typeof networkRegistryLocationSchema>;
export type FileSystemRegistryLocation = z.infer<typeof fileSystemRegistryLocationSchema>;

export type DockerImageId = z.infer<typeof dockerImageIdSchema>;

export type DockerImageProviderLocation = z.infer<typeof dockerImageProviderLocationSchema>;
export type NetworkProviderLocation = z.infer<typeof networkProviderLocationSchema>;

export type ResolvedGitHubUrl = z.infer<typeof resolvedGitHubUrlSchema>;
export type ResolvedDockerImageId = z.infer<typeof resolvedDockerImageIdSchema>;
