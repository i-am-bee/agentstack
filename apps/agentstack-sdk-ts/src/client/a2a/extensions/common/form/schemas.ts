/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const baseFieldSchema = z.object({
  id: z.string().nonempty(),
  label: z.string().nonempty(),
  required: z.boolean().nullish(),
  col_span: z.int().min(1).max(4).nullish(),
});

export const textFieldSchema = baseFieldSchema.extend({
  type: z.literal('text'),
  placeholder: z.string().nullish(),
  default_value: z.string().nullish(),
  auto_resize: z.boolean().default(true).nullish(),
});

export const dateFieldSchema = baseFieldSchema.extend({
  type: z.literal('date'),
  placeholder: z.string().nullish(),
  default_value: z.string().nullish(),
});

export const fileFieldSchema = baseFieldSchema.extend({
  type: z.literal('file'),
  accept: z.array(z.string()),
});

export const selectFieldOptionSchema = z.object({
  id: z.string().nonempty(),
  label: z.string().nonempty(),
});

export const singleSelectFieldSchema = baseFieldSchema.extend({
  type: z.literal('singleselect'),
  options: z.array(selectFieldOptionSchema).nonempty(),
  default_value: z.string().nullish(),
});

export const multiSelectFieldSchema = baseFieldSchema.extend({
  type: z.literal('multiselect'),
  options: z.array(selectFieldOptionSchema).nonempty(),
  default_value: z.array(z.string()).nullish(),
});

export const checkboxFieldSchema = baseFieldSchema.extend({
  type: z.literal('checkbox'),
  content: z.string(),
  default_value: z.boolean().nullish(),
});

export const checkboxGroupFieldSchema = baseFieldSchema.extend({
  type: z.literal('checkbox_group'),
  fields: z.array(checkboxFieldSchema),
});

export const formFieldSchema = z.discriminatedUnion('type', [
  textFieldSchema,
  dateFieldSchema,
  fileFieldSchema,
  singleSelectFieldSchema,
  multiSelectFieldSchema,
  checkboxFieldSchema,
  checkboxGroupFieldSchema,
]);

export const textFieldValueSchema = z.object({
  type: textFieldSchema.shape.type,
  value: z.string().nullish(),
});

export const dateFieldValueSchema = z.object({
  type: dateFieldSchema.shape.type,
  value: z.string().nullish(),
});

export const fileFieldValueSchema = z.object({
  type: fileFieldSchema.shape.type,
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

export const singleSelectFieldValueSchema = z.object({
  type: singleSelectFieldSchema.shape.type,
  value: z.string().nullish(),
});

export const multiSelectFieldValueSchema = z.object({
  type: multiSelectFieldSchema.shape.type,
  value: z.array(z.string()).nullish(),
});

export const checkboxFieldValueSchema = z.object({
  type: checkboxFieldSchema.shape.type,
  value: z.boolean().nullish(),
});

export const checkboxGroupFieldValueSchema = z.object({
  type: checkboxGroupFieldSchema.shape.type,
  value: z.record(z.string(), z.boolean().nullish()).nullish(),
});

export const formFieldValueSchema = z.discriminatedUnion('type', [
  textFieldValueSchema,
  dateFieldValueSchema,
  fileFieldValueSchema,
  singleSelectFieldValueSchema,
  multiSelectFieldValueSchema,
  checkboxFieldValueSchema,
  checkboxGroupFieldValueSchema,
]);

export const formRenderSchema = z.object({
  fields: z.array(formFieldSchema).nonempty(),
  title: z.string().nullish(),
  description: z.string().nullish(),
  columns: z.int().min(1).max(4).nullish(),
  submit_label: z.string().nullish(),
});

export const formValuesSchema = z.record(z.string(), formFieldValueSchema);

export const formResponseSchema = z.object({
  values: formValuesSchema,
});
