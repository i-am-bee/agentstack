/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type {
  uiElementSchema,
  generativeInterfaceDemandsSchema,
  generativeInterfaceFulfillmentsSchema,
  generativeInterfaceResponseSchema,
  generativeInterfaceSpecSchema,
} from './schemas';

export type UIElement = z.infer<typeof uiElementSchema>;

export type GenerativeInterfaceSpec = z.infer<typeof generativeInterfaceSpecSchema>;

export type GenerativeInterfaceResponse = z.infer<typeof generativeInterfaceResponseSchema>;

export type GenerativeInterfaceDemands = z.infer<typeof generativeInterfaceDemandsSchema>;

export type GenerativeInterfaceFulfillments = z.infer<typeof generativeInterfaceFulfillmentsSchema>;
