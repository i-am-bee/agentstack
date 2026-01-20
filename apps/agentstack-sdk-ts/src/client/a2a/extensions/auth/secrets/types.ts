/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type {
  secretDemandSchema,
  secretDemandsSchema,
  secretFulfillmentSchema,
  secretFulfillmentsSchema,
} from './schemas';

export type SecretDemand = z.infer<typeof secretDemandSchema>;
export type SecretDemands = z.infer<typeof secretDemandsSchema>;

export type SecretFulfillment = z.infer<typeof secretFulfillmentSchema>;
export type SecretFulfillments = z.infer<typeof secretFulfillmentsSchema>;
