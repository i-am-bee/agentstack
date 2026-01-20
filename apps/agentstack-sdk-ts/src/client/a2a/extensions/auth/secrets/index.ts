/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import type { A2AServiceExtension, A2AUiExtension } from '../../../../core/extensions/types';
import { secretDemandsSchema, secretFulfillmentsSchema } from './schemas';
import type { SecretDemands, SecretFulfillments } from './types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/auth/secrets/v1';

export const secretsExtension: A2AServiceExtension<typeof URI, SecretDemands, SecretFulfillments> = {
  getUri: () => URI,
  getDemandsSchema: () => secretDemandsSchema,
  getFulfillmentsSchema: () => secretFulfillmentsSchema,
};

export const secretsRequestExtension: A2AUiExtension<typeof URI, SecretDemands> = {
  getUri: () => URI,
  getMessageMetadataSchema: () => z.object({ [URI]: secretDemandsSchema }).partial(),
};
