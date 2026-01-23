/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import type { A2AServiceExtension, A2AUiExtension } from '../../../../core/extensions/types';
import { oauthDemandsSchema, oauthFulfillmentsSchema, oauthRequestSchema } from './schemas';
import type { OAuthDemands, OAuthFulfillments, OAuthRequest } from './types';

export const OAUTH_EXTENSION_URI = 'https://a2a-extensions.agentstack.beeai.dev/auth/oauth/v1';

export const oauthExtension: A2AServiceExtension<typeof OAUTH_EXTENSION_URI, OAuthDemands, OAuthFulfillments> = {
  getUri: () => OAUTH_EXTENSION_URI,
  getDemandsSchema: () => oauthDemandsSchema,
  getFulfillmentsSchema: () => oauthFulfillmentsSchema,
};

export const oauthRequestExtension: A2AUiExtension<typeof OAUTH_EXTENSION_URI, OAuthRequest> = {
  getUri: () => OAUTH_EXTENSION_URI,
  getMessageMetadataSchema: () => z.object({ [OAUTH_EXTENSION_URI]: oauthRequestSchema }).partial(),
};
