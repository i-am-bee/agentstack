/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FormField } from 'agentstack-sdk';
import get from 'lodash/get';
import type { FormState, RegisterOptions } from 'react-hook-form';

import { REQUIRED_ERROR_MESSAGE } from '../constants';
import type { ValuesOfField } from '../types';
import { getFieldName } from '../utils';

export function useFormFieldValidation<F extends FormField>({
  field,
  formState,
  name,
  rules: customRules,
}: {
  field: F;
  formState: FormState<ValuesOfField<F>>;
  name?: string;
  rules?: RegisterOptions;
}) {
  const { required } = field;

  const fieldName = name ?? getFieldName(field);
  const error = get(formState.errors, fieldName);
  const invalid = Boolean(error);
  const invalidText = error?.message;

  const rules = {
    required: Boolean(required) && REQUIRED_ERROR_MESSAGE,
    ...customRules,
  };

  return {
    rules,
    invalid,
    invalidText,
  };
}
