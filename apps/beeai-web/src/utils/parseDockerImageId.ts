/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

const pattern = new RegExp(
  [
    // Registry (optional) - ends with slash and contains at least one dot
    '((?<registry>[^/]+\\.[^/]+)/)?',

    // Repository (required) - final component before any tag
    '(?<repository>[^:]+)',

    // Tag (optional) - everything after the colon
    '(?::(?<tag>[^:]+))?',
  ].join(''),
);

type ParsedDockerImageId = {
  registry: string;
  repository: string;
  tag: string;
};

export function parseDockerImageId(dockerImageId: string): ParsedDockerImageId {
  const match = pattern.exec(dockerImageId);

  if (!match?.groups) {
    throw new Error(`Invalid Docker image: ${dockerImageId}`);
  }

  const { registry = 'ghcr.io', repository, tag = 'latest' } = match.groups;

  return {
    registry,
    repository,
    tag,
  };
}
