/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export function isApiAgentManifestUrl(url: string) {
  return AGENT_MANIFEST_PATH_REGEX.test(url);
}

export function isUrlTrailingSlashNeeded(url: string) {
  return A2A_JSONRPC_PATH_REGEX.test(url);
}

const AGENT_MANIFEST_PATH_REGEX = /v1\/a2a\/.*\/\.well-known\/agent\-card\.json/;
const A2A_JSONRPC_PATH_REGEX = /v1\/a2a\/.*\/\jsonrpc/;
