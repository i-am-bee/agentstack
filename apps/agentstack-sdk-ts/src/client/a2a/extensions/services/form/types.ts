/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type {
  formDemandsSchema,
  formFulfillmentsSchema,
  settingsFormFieldSchema,
  settingsFormFieldValueSchema,
  settingsFormRenderSchema,
  settingsFormResponseSchema,
  settingsFormValuesSchema,
} from './schemas';

export type SettingsFormField = z.infer<typeof settingsFormFieldSchema>;
export type SettingsFormFieldValue = z.infer<typeof settingsFormFieldValueSchema>;

export type SettingsFormRender = z.infer<typeof settingsFormRenderSchema>;
export type SettingsFormValues = z.infer<typeof settingsFormValuesSchema>;
export type SettingsFormResponse = z.infer<typeof settingsFormResponseSchema>;

export type FormDemands = z.infer<typeof formDemandsSchema>;
export type FormFulfillments = z.infer<typeof formFulfillmentsSchema>;
