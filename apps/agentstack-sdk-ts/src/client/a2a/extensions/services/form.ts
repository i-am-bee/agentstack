/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import { formRenderSchema, responseSchema } from '../common/form';
import type { A2AServiceExtension } from '../types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/services/form/v1';

const formDemandSchema = z.object({
  form_demands: z
    .object({
      initial_form: formRenderSchema,
      // TOOD: extra keys
    })
    .partial(),
});
export type FormDemands = z.infer<typeof formDemandSchema>;

const formFulfillmentSchema = z.object({
  form_fulfillments: z.record(z.string(), responseSchema),
});
export type FormFulfillments = z.infer<typeof formFulfillmentSchema>;

export const formExtension: A2AServiceExtension<typeof URI, z.infer<typeof formDemandSchema>, FormFulfillments> = {
  getDemandsSchema: () => formDemandSchema,
  getFulfillmentSchema: () => formFulfillmentSchema,
  getUri: () => URI,
};
