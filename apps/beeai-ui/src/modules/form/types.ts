/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FormField, FormResponseValue } from '#api/a2a/extensions/ui/form.ts';

export type RunFormValues = Record<string, FormResponseValue>;

export type ValueOfField<F extends FormField> = Extract<FormResponseValue, { type: F['type'] }>;
export type ValuesOfField<F extends FormField> = Record<string, ValueOfField<F>>;
