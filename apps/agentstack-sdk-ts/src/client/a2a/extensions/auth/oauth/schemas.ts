/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const oAuthDemandSchema = z.object({
  redirect_uri: z.boolean(),
});

export const oAuthDemandsSchema = z.object({
  oauth_demands: z.record(z.string(), oAuthDemandSchema),
});

export const oAuthFulfillmentSchema = z.object({
  redirect_uri: z.string(),
});

export const oAuthFulfillmentsSchema = z.object({
  oauth_fulfillments: z.record(z.string(), oAuthFulfillmentSchema),
});

export const oAuthRequestSchema = z.object({
  authorization_endpoint_url: z.string(),
});

export const oAuthResponseSchema = z.object({
  redirect_uri: z.string(),
});

export const oAuthMessageSchema = z.object({
  data: oAuthResponseSchema,
});
