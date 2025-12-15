/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type {
  settingsCheckboxFieldSchema,
  settingsCheckboxFieldValueSchema,
  settingsCheckboxGroupFieldSchema,
  settingsCheckboxGroupFieldValueSchema,
  settingsDemandsSchema,
  settingsFieldSchema,
  settingsFieldValueSchema,
  settingsFulfillmentsSchema,
  settingsOptionItemSchema,
  settingsSingleSelectFieldSchema,
  settingsSingleSelectFieldValueSchema,
  settingsValuesSchema,
} from './schemas';

export type SettingsCheckboxField = z.infer<typeof settingsCheckboxFieldSchema>;
export type SettingsCheckboxGroupField = z.infer<typeof settingsCheckboxGroupFieldSchema>;
export type SettingsOptionItem = z.infer<typeof settingsOptionItemSchema>;
export type SettingsSingleSelectField = z.infer<typeof settingsSingleSelectFieldSchema>;

export type SettingsField = z.infer<typeof settingsFieldSchema>;

export type SettingsCheckboxFieldValue = z.infer<typeof settingsCheckboxFieldValueSchema>;
export type SettingsCheckboxGroupFieldValue = z.infer<typeof settingsCheckboxGroupFieldValueSchema>;
export type SettingsSingleSelectFieldValue = z.infer<typeof settingsSingleSelectFieldValueSchema>;

export type SettingsFieldValue = z.infer<typeof settingsFieldValueSchema>;

export type SettingsDemands = z.infer<typeof settingsDemandsSchema>;
export type SettingsValues = z.infer<typeof settingsValuesSchema>;
export type SettingsFulfillments = z.infer<typeof settingsFulfillmentsSchema>;
