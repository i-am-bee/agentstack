/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Checkbox } from '@carbon/react';
import type { CheckboxField, CheckboxGroupField } from 'agentstack-sdk';
import { useFormContext } from 'react-hook-form';

import { useFormFieldValidation } from '#modules/form/hooks/useFormFieldValidation.ts';
import type { ValuesOfField } from '#modules/form/types.ts';
import { getFieldName } from '#modules/form/utils.ts';

interface Props {
  field: CheckboxField;
  groupField: CheckboxGroupField;
}

export function CheckboxGroupFieldItem({ field, groupField }: Props) {
  const { id, content } = field;

  const groupName = getFieldName(groupField);
  const name = `${groupName}.${id}`;

  const { register, formState } = useFormContext<ValuesOfField<CheckboxField>>();
  const { rules, invalid, invalidText } = useFormFieldValidation({ field, formState, name });

  const inputProps = register(name, {
    ...rules,
    deps: groupName,
  });

  return <Checkbox id={name} labelText={content} invalid={invalid} invalidText={invalidText} {...inputProps} />;
}
