/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export function isApiAgentManifestPath(path: string[]) {
  return AGENT_MANIFEST_PATH_REGEX.test(path.join('/'));
}

const AGENT_MANIFEST_PATH_REGEX = /v1\/a2a\/.*\/\.well-known\/agent\.json/;
