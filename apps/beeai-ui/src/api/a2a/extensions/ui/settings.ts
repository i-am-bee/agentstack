/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import type { A2AServiceExtension } from '../types';

const URI = 'https://a2a-extensions.beeai.dev/ui/settings/v1';

const baseField = z.object({
  id: z.string().nonempty(),
  label: z.string().nonempty(),
});

const checkboxField = baseField.extend({
  type: z.literal('checkbox'),
  default_value: z.boolean(),
});

const checkboxFieldValue = z.object({
  type: checkboxField.shape.type,
  value: z.boolean().nullish(),
});

const fieldSchema = z.discriminatedUnion('type', [checkboxField]);

const settingsRenderSchema = z.object({
  fields: z.array(fieldSchema).nonempty(),
});

const settingsValuesSchema = z.object({
  id: z.string().nonempty(),
  values: z.record(z.discriminatedUnion('type', [checkboxFieldValue])),
});

export type CheckboxField = z.infer<typeof checkboxField>;

export type SettingsRender = z.infer<typeof settingsRenderSchema>;
export type SettingsValues = z.infer<typeof settingsValuesSchema>;
export type SettingsResponseValue = SettingsValues['values'][string];

export const settingsExtension: A2AServiceExtension<
  typeof URI,
  z.infer<typeof settingsRenderSchema>,
  SettingsValues
> = {
  getDemandsSchema: () => settingsRenderSchema,
  getFulfillmentSchema: () => settingsValuesSchema,
  getUri: () => URI,
};
