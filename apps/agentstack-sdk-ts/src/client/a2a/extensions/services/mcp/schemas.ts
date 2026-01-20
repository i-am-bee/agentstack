/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import { MCPTransportType } from './types';

export const mcpTransportTypeSchema = z.enum(MCPTransportType);

export const mcpDemandSchema = z.object({
  description: z.string().nullish(),
  suggested: z.array(z.string()).nullish(),
  allowed_transports: z.array(mcpTransportTypeSchema).nullish(),
});

export const mcpDemandsSchema = z.object({
  mcp_demands: z.record(z.string(), mcpDemandSchema),
});

export const mcpFulfillmentSchema = z.object({
  transport: z.object({
    type: mcpTransportTypeSchema,
    url: z.string(),
    headers: z.record(z.string(), z.string()).optional(),
  }),
});

export const mcpFulfillmentsSchema = z.object({
  mcp_fulfillments: z.record(z.string(), mcpFulfillmentSchema),
});
