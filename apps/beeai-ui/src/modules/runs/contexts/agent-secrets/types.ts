/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { SecretDemand } from 'agentstack-sdk';

export type ReadySecretDemand = SecretDemand & { isReady: true; value: string; key: string };
export type NonReadySecretDemand = SecretDemand & { isReady: false };
export type AgentSecret = SecretDemand & { key: string } & (ReadySecretDemand | NonReadySecretDemand);

export type AgentRequestSecrets = Record<string, ReadySecretDemand | NonReadySecretDemand>;
