/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const settingsCheckboxFieldSchema = z.object({
  id: z.string().nonempty(),
  label: z.string().nonempty(),
  default_value: z.boolean(),
});

export const settingsCheckboxGroupFieldSchema = z.object({
  id: z.string().nonempty(),
  type: z.literal('checkbox_group'),
  fields: z.array(settingsCheckboxFieldSchema),
});

export const settingsOptionItemSchema = z.object({
  label: z.string().nonempty(),
  value: z.string().nonempty(),
});

export const settingsSingleSelectFieldSchema = z.object({
  type: z.literal('single_select'),
  id: z.string().nonempty(),
  label: z.string().nonempty(),
  options: z.array(settingsOptionItemSchema).nonempty(),
  default_value: z.string().nonempty(),
});

export const settingsFieldSchema = z.discriminatedUnion('type', [
  settingsCheckboxGroupFieldSchema,
  settingsSingleSelectFieldSchema,
]);

export const settingsCheckboxFieldValueSchema = z.object({
  value: z.boolean(),
});

export const settingsCheckboxGroupFieldValueSchema = z.object({
  type: z.literal('checkbox_group'),
  values: z.record(z.string(), settingsCheckboxFieldValueSchema),
});

export const settingsSingleSelectFieldValueSchema = z.object({
  type: z.literal('single_select'),
  value: z.string(),
});

export const settingsFieldValueSchema = z.discriminatedUnion('type', [
  settingsCheckboxGroupFieldValueSchema,
  settingsSingleSelectFieldValueSchema,
]);

export const settingsDemandsSchema = z.object({
  fields: z.array(settingsFieldSchema),
});

export const settingsValuesSchema = z.record(z.string(), settingsFieldValueSchema);

export const settingsFulfillmentsSchema = z.object({
  values: settingsValuesSchema,
});
