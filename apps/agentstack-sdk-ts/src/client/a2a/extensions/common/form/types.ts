/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type {
  checkboxFieldSchema,
  checkboxFieldValueSchema,
  dateFieldSchema,
  dateFieldValueSchema,
  fileFieldSchema,
  fileFieldValueSchema,
  formFieldSchema,
  formFieldValueSchema,
  formRenderSchema,
  formResponseSchema,
  formValuesSchema,
  multiSelectFieldSchema,
  multiSelectFieldValueSchema,
  selectFieldOptionSchema,
  singleSelectFieldSchema,
  singleSelectFieldValueSchema,
  textFieldSchema,
  textFieldValueSchema,
} from './schemas';

export type TextField = z.infer<typeof textFieldSchema>;
export type DateField = z.infer<typeof dateFieldSchema>;
export type FileField = z.infer<typeof fileFieldSchema>;
export type SelectFieldOption = z.infer<typeof selectFieldOptionSchema>;
export type SingleSelectField = z.infer<typeof singleSelectFieldSchema>;
export type MultiSelectField = z.infer<typeof multiSelectFieldSchema>;
export type CheckboxField = z.infer<typeof checkboxFieldSchema>;

export type FormField = z.infer<typeof formFieldSchema>;

export type TextFieldValue = z.infer<typeof textFieldValueSchema>;
export type DateFieldValue = z.infer<typeof dateFieldValueSchema>;
export type FileFieldValue = z.infer<typeof fileFieldValueSchema>;
export type SingleSelectFieldValue = z.infer<typeof singleSelectFieldValueSchema>;
export type MultiSelectFieldValue = z.infer<typeof multiSelectFieldValueSchema>;
export type CheckboxFieldValue = z.infer<typeof checkboxFieldValueSchema>;

export type FormFieldValue = z.infer<typeof formFieldValueSchema>;

export type FormRender = z.infer<typeof formRenderSchema>;
export type FormValues = z.infer<typeof formValuesSchema>;
export type FormResponse = z.infer<typeof formResponseSchema>;
