/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import type { A2AServiceExtension, A2AUiExtension } from '../../../../core/extensions/types';
import { oAuthDemandsSchema, oAuthFulfillmentsSchema, oAuthRequestSchema } from './schemas';
import type { OAuthDemands, OAuthFulfillments, OAuthRequest } from './types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/auth/oauth/v1';

export const oAuthExtension: A2AServiceExtension<typeof URI, OAuthDemands, OAuthFulfillments> = {
  getUri: () => URI,
  getDemandsSchema: () => oAuthDemandsSchema,
  getFulfillmentsSchema: () => oAuthFulfillmentsSchema,
};

export const oAuthRequestExtension: A2AUiExtension<typeof URI, OAuthRequest> = {
  getUri: () => URI,
  getMessageMetadataSchema: () => z.object({ [URI]: oAuthRequestSchema }).partial(),
};
