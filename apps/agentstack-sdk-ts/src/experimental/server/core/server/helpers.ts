/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export function createAgentCardUrl(host: string, port: number, selfRegistrationId?: string) {
  return `http://${host === '0.0.0.0' ? 'localhost' : host}:${port}${selfRegistrationId ? `#${selfRegistrationId}` : ''}`;
}

export function normalizeDockerHost(host: string) {
  return host.replace(/0\.0\.0\.0|localhost|127\.0\.0\.1/g, 'host.docker.internal');
}
