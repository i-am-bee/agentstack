/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Select, SelectItem } from '@carbon/react';
import type { SingleSelectField } from 'agentstack-sdk';
import { useFormContext } from 'react-hook-form';

import { useFormFieldValidation } from '#modules/form/hooks/useFormFieldValidation.ts';
import type { ValuesOfField } from '#modules/form/types.ts';
import { getFieldName } from '#modules/form/utils.ts';

interface Props {
  field: SingleSelectField;
}

export function SingleSelectField({ field }: Props) {
  const { id, label, options } = field;

  const { register, formState } = useFormContext<ValuesOfField<SingleSelectField>>();
  const { rules, invalid, invalidText } = useFormFieldValidation({ field, formState });

  const inputProps = register(getFieldName(field), rules);

  return (
    <Select id={id} size="lg" labelText={label} invalid={invalid} invalidText={invalidText} {...inputProps}>
      {options.map(({ id, label }) => (
        <SelectItem key={id} text={label} value={id} />
      ))}
    </Select>
  );
}
