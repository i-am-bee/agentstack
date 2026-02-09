/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export function getAgentCardPath(providerId: string) {
  return `api/v1/a2a/${providerId}/.well-known/agent-card.json`;
}
