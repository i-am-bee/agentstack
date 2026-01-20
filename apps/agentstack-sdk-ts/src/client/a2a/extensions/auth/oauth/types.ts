/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type {
  oauthDemandSchema,
  oauthDemandsSchema,
  oauthFulfillmentSchema,
  oauthFulfillmentsSchema,
  oauthMessageSchema,
  oauthRequestSchema,
  oauthResponseSchema,
} from './schemas';

export type OAuthDemand = z.infer<typeof oauthDemandSchema>;
export type OAuthDemands = z.infer<typeof oauthDemandsSchema>;

export type OAuthFulfillment = z.infer<typeof oauthFulfillmentSchema>;
export type OAuthFulfillments = z.infer<typeof oauthFulfillmentsSchema>;

export type OAuthRequest = z.infer<typeof oauthRequestSchema>;
export type OAuthResponse = z.infer<typeof oauthResponseSchema>;

export type OAuthMessage = z.infer<typeof oauthMessageSchema>;
