/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import type { A2AServiceExtension, A2AUiExtension } from '../types';

const URI = 'https://a2a-extensions.beeai.dev/ui/form/v1';

const baseField = z.object({
  id: z.string().nonempty(),
  label: z.string().nonempty(),
  required: z.boolean(),
  col_span: z.int().min(1).max(4).nullish(),
});

const textField = baseField.extend({
  type: z.literal('text'),
  placeholder: z.string().nullish(),
  default_value: z.string().nullish(),
  auto_resize: z.boolean().default(true).nullish(),
});

const textFieldValue = z.object({
  type: textField.shape.type,
  value: z.string().nullish(),
});

const dateField = baseField.extend({
  type: z.literal('date'),
  placeholder: z.string().nullish(),
  default_value: z.string().nullish(),
});

const dateFieldValue = z.object({
  type: dateField.shape.type,
  value: z.string().nullish(),
});

const fileField = baseField.extend({
  type: z.literal('file'),
  accept: z.array(z.string()),
});

const fileFieldValue = z.object({
  type: fileField.shape.type,
  value: z
    .array(
      z.object({
        uri: z.string(),
        name: z.string().nullish(),
        mime_type: z.string().nullish(),
      }),
    )
    .nullish(),
});

const singleSelectField = baseField.extend({
  type: z.literal('singleselect'),
  options: z
    .array(
      z.object({
        id: z.string().nonempty(),
        label: z.string().nonempty(),
      }),
    )
    .nonempty(),
  default_value: z.string().nullish(),
});

const singleSelectFieldValue = z.object({
  type: singleSelectField.shape.type,
  value: z.string().nullish(),
});

const multiSelectField = baseField.extend({
  type: z.literal('multiselect'),
  options: z
    .array(
      z.object({
        id: z.string().nonempty(),
        label: z.string().nonempty(),
      }),
    )
    .nonempty(),
  default_value: z.array(z.string()).nullish(),
});

const multiSelectFieldValue = z.object({
  type: multiSelectField.shape.type,
  value: z.array(z.string()).nullish(),
});

const checkboxField = baseField.extend({
  type: z.literal('checkbox'),
  content: z.string(),
  default_value: z.boolean(),
});

const checkboxFieldValue = z.object({
  type: checkboxField.shape.type,
  value: z.boolean().nullish(),
});

const fieldSchema = z.discriminatedUnion('type', [
  textField,
  dateField,
  fileField,
  singleSelectField,
  multiSelectField,
  checkboxField,
]);

const renderSchema = z.object({
  id: z.string().nonempty(),
  title: z.string().nullish(),
  description: z.string().nullish(),
  columns: z.int().min(1).max(4).nullish(),
  submit_label: z.string().nullish(),
  fields: z.array(fieldSchema).nonempty(),
});

const responseSchema = z.object({
  id: z.string().nonempty(),
  values: z.record(
    z.string(),
    z.discriminatedUnion('type', [
      textFieldValue,
      dateFieldValue,
      fileFieldValue,
      singleSelectFieldValue,
      multiSelectFieldValue,
      checkboxFieldValue,
    ]),
  ),
});

export type TextField = z.infer<typeof textField>;
export type DateField = z.infer<typeof dateField>;
export type FileField = z.infer<typeof fileField>;
export type SingleSelectField = z.infer<typeof singleSelectField>;
export type MultiSelectField = z.infer<typeof multiSelectField>;
export type CheckboxField = z.infer<typeof checkboxField>;

export type FormField = z.infer<typeof fieldSchema>;

export type FormDemands = z.infer<typeof renderSchema>;
export type FormFullfillments = z.infer<typeof responseSchema>;
export type FormResponseValue = FormFullfillments['values'][string];

export const formMessageExtension: A2AUiExtension<typeof URI, FormDemands> = {
  getMessageMetadataSchema: () => z.object({ [URI]: renderSchema }).partial(),
  getUri: () => URI,
};
export const formExtension: A2AServiceExtension<typeof URI, z.infer<typeof renderSchema>, FormFullfillments> = {
  getDemandsSchema: () => renderSchema,
  getFulfillmentSchema: () => responseSchema,
  getUri: () => URI,
};
