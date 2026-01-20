/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const oauthDemandSchema = z.object({
  redirect_uri: z.boolean(),
});

export const oauthDemandsSchema = z.object({
  oauth_demands: z.record(z.string(), oauthDemandSchema),
});

export const oauthFulfillmentSchema = z.object({
  redirect_uri: z.string(),
});

export const oauthFulfillmentsSchema = z.object({
  oauth_fulfillments: z.record(z.string(), oauthFulfillmentSchema),
});

export const oauthRequestSchema = z.object({
  authorization_endpoint_url: z.string(),
});

export const oauthResponseSchema = z.object({
  redirect_uri: z.string(),
});

export const oauthMessageSchema = z.object({
  data: oauthResponseSchema,
});
