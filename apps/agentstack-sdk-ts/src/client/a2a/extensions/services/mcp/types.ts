/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type { mcpDemandSchema, mcpDemandsSchema, mcpFulfillmentSchema, mcpFulfillmentsSchema } from './schemas';

export enum MCPTransportType {
  StreamableHttp = 'streamable_http',
  Stdio = 'stdio',
}

export type MCPDemand = z.infer<typeof mcpDemandSchema>;
export type MCPDemands = z.infer<typeof mcpDemandsSchema>;

export type MCPFulfillment = z.infer<typeof mcpFulfillmentSchema>;
export type MCPFulfillments = z.infer<typeof mcpFulfillmentsSchema>;
