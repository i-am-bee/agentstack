/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { SecretDemand } from '#api/a2a/extensions/services/secrets.ts';

export type ReadySecretDemand = SecretDemand & { isReady: true; value: string };
export type NonReadySecretDemand = SecretDemand & { isReady: false };

export type AgentRequestedApiKeys = Record<string, SecretDemand & (ReadySecretDemand | NonReadySecretDemand)>;
