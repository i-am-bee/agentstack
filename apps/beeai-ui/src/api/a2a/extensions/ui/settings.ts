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
  values: z.record(checkboxFieldValue),
});

const singleSelectFieldValue = z.object({
  type: z.literal('single_select'),
  value: z.string(),
});

const settingsFieldValue = z.discriminatedUnion('type', [checkboxGroupFieldValue, singleSelectFieldValue]);

export const agentSettings = z.record(settingsFieldValue);
export type AgentSettings = z.infer<typeof agentSettings>;

const agentRunSettingsSchema = z.object({
  values: agentSettings,
});

export type CheckboxField = z.infer<typeof checkboxField>;
export type CheckboxGroupField = z.infer<typeof checkboxGroupField>;
export type OptionItem = z.infer<typeof optionItem>;
export type SingleSelectField = z.infer<typeof singleSelectField>;
export type CheckboxFieldValue = z.infer<typeof checkboxFieldValue>;
export type CheckboxGroupFieldValue = z.infer<typeof checkboxGroupFieldValue>;
export type SingleSelectFieldValue = z.infer<typeof singleSelectFieldValue>;
export type SettingsFieldValue = z.infer<typeof settingsFieldValue>;

export type SettingsRender = z.infer<typeof settingsRenderSchema>;
export type AgentRunSettings = z.infer<typeof agentRunSettingsSchema>;

export const settingsExtension: A2AServiceExtension<
  typeof URI,
  z.infer<typeof settingsRenderSchema>,
  AgentRunSettings
> = {
  getDemandsSchema: () => settingsRenderSchema,
  getFulfillmentSchema: () => agentRunSettingsSchema,
  getUri: () => URI,
};
