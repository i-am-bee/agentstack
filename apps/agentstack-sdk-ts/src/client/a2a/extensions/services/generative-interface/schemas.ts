/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const uiElementSchema = z.object({
  key: z.string(),
  type: z.string(),
  props: z.record(z.string(), z.unknown()).default({}),
  children: z.array(z.string()).default([]),
});

export const generativeInterfaceSpecSchema = z.object({
  root: z.string(),
  elements: z.record(z.string(), uiElementSchema),
});

export const generativeInterfaceResponseSchema = z.object({
  component_id: z.string(),
  event_type: z.string(),
  payload: z.record(z.string(), z.unknown()).optional(),
});

export const generativeInterfaceDemandsSchema = z.object({
  generative_interface_demands: z.object({}).optional(),
});

export const generativeInterfaceFulfillmentsSchema = z.object({
  generative_interface_fulfillments: z.object({
    catalog_prompt: z.string(),
  }),
});
