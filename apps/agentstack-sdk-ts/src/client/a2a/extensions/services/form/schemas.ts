/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import { formRenderSchema, formResponseSchema } from '../../common/form/schemas';

export const formDemandsSchema = z.object({
  form_demands: z
    .object({
      initial_form: formRenderSchema,
    })
    .partial(),
});

export const formFulfillmentsSchema = z.object({
  form_fulfillments: z.record(z.string(), formResponseSchema),
});
