/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import type { A2AServiceExtension, A2AUiExtension } from '../../../../core/extensions/types';
import { secretDemandsSchema, secretFulfillmentsSchema } from './schemas';
import type { SecretDemands, SecretFulfillments } from './types';

export const SECRETS_EXTENSION_URI = 'https://a2a-extensions.agentstack.beeai.dev/auth/secrets/v1';

export const secretsExtension: A2AServiceExtension<typeof SECRETS_EXTENSION_URI, SecretDemands, SecretFulfillments> = {
  getUri: () => SECRETS_EXTENSION_URI,
  getDemandsSchema: () => secretDemandsSchema,
  getFulfillmentsSchema: () => secretFulfillmentsSchema,
};

export const secretsRequestExtension: A2AUiExtension<typeof SECRETS_EXTENSION_URI, SecretDemands> = {
  getUri: () => SECRETS_EXTENSION_URI,
  getMessageMetadataSchema: () => z.object({ [SECRETS_EXTENSION_URI]: secretDemandsSchema }).partial(),
};
