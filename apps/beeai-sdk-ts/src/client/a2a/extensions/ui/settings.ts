/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import type { A2AServiceExtension } from '../types';

const URI = 'https://a2a-extensions.beeai.dev/ui/settings/v1';

const checkboxField = z.object({
  id: z.string().nonempty(),
  label: z.string().nonempty(),
  default_value: z.boolean(),
});

const checkboxGroupField = z.object({
  id: z.string().nonempty(),
  type: z.literal('checkbox_group'),
  fields: z.array(checkboxField),
});

const optionItem = z.object({
  label: z.string().nonempty(),
  value: z.string().nonempty(),
});

const singleSelectField = z.object({
  type: z.literal('single_select'),
  id: z.string().nonempty(),
  label: z.string().nonempty(),
  options: z.array(optionItem).nonempty(),
  default_value: z.string().nonempty(),
});

const settingsRenderSchema = z.object({
  fields: z.array(z.discriminatedUnion('type', [checkboxGroupField, singleSelectField])),
});

const checkboxFieldValue = z.object({
  value: z.boolean(),
});

const checkboxGroupFieldValue = z.object({
  type: z.literal('checkbox_group'),
  values: z.record(z.string(), checkboxFieldValue),
});

const singleSelectFieldValue = z.object({
  type: z.literal('single_select'),
  value: z.string(),
});

const settingsFieldValue = z.discriminatedUnion('type', [checkboxGroupFieldValue, singleSelectFieldValue]);

export const agentSettings = z.record(z.string(), settingsFieldValue);
export type AgentSettings = z.infer<typeof agentSettings>;

const agentRunSettingsSchema = z.object({
  values: agentSettings,
});

export type SettingsCheckboxField = z.infer<typeof checkboxField>;
export type SettingsCheckboxGroupField = z.infer<typeof checkboxGroupField>;
export type SettingsOptionItem = z.infer<typeof optionItem>;
export type SettingsSingleSelectField = z.infer<typeof singleSelectField>;
export type SettingsCheckboxFieldValue = z.infer<typeof checkboxFieldValue>;
export type SettingsCheckboxGroupFieldValue = z.infer<typeof checkboxGroupFieldValue>;
export type SettingsSingleSelectFieldValue = z.infer<typeof singleSelectFieldValue>;
export type SettingsFieldValue = z.infer<typeof settingsFieldValue>;

export type SettingsDemands = z.infer<typeof settingsRenderSchema>;
export type SettingsFullfillments = z.infer<typeof agentRunSettingsSchema>;

export const settingsExtension: A2AServiceExtension<
  typeof URI,
  z.infer<typeof settingsRenderSchema>,
  SettingsFullfillments
> = {
  getDemandsSchema: () => settingsRenderSchema,
  getFulfillmentSchema: () => agentRunSettingsSchema,
  getUri: () => URI,
};
