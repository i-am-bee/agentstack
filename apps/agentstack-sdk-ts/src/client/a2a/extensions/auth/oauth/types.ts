/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type {
  oAuthDemandSchema,
  oAuthDemandsSchema,
  oAuthFulfillmentSchema,
  oAuthFulfillmentsSchema,
  oAuthMessageSchema,
  oAuthRequestSchema,
  oAuthResponseSchema,
} from './schemas';

export type OAuthDemand = z.infer<typeof oAuthDemandSchema>;
export type OAuthDemands = z.infer<typeof oAuthDemandsSchema>;

export type OAuthFulfillment = z.infer<typeof oAuthFulfillmentSchema>;
export type OAuthFulfillments = z.infer<typeof oAuthFulfillmentsSchema>;

export type OAuthRequest = z.infer<typeof oAuthRequestSchema>;
export type OAuthResponse = z.infer<typeof oAuthResponseSchema>;

export type OAuthMessage = z.infer<typeof oAuthMessageSchema>;
