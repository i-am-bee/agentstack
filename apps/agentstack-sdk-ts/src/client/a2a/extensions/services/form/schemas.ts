/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import {
  checkboxGroupFieldSchema,
  checkboxGroupFieldValueSchema,
  formRenderSchema,
  formResponseSchema,
  singleSelectFieldSchema,
  singleSelectFieldValueSchema,
} from '../../common/form/schemas';

export const settingsFormFieldSchema = z.discriminatedUnion('type', [
  checkboxGroupFieldSchema,
  singleSelectFieldSchema,
]);

export const settingsFormFieldValueSchema = z.discriminatedUnion('type', [
  checkboxGroupFieldValueSchema,
  singleSelectFieldValueSchema,
]);

export const settingsFormRenderSchema = formRenderSchema.extend({
  fields: z.array(settingsFormFieldSchema).nonempty(),
});

export const settingsFormValuesSchema = z.record(z.string(), settingsFormFieldValueSchema);

export const settingsFormResponseSchema = formResponseSchema.extend({
  values: settingsFormValuesSchema,
});

export const formDemandsSchema = z.object({
  form_demands: z
    .object({
      initial_form: formRenderSchema,
      settings_form: settingsFormRenderSchema,
    })
    .partial()
    .catchall(formRenderSchema),
});

export const formFulfillmentsSchema = z.object({
  form_fulfillments: z
    .object({
      initial_form: formResponseSchema,
      settings_form: settingsFormResponseSchema,
    })
    .partial()
    .catchall(formResponseSchema),
});
