/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Select, SelectItem } from '@carbon/react';
import type { SingleSelectField } from 'agentstack-sdk';
import { useId } from 'react';
import { useFormContext } from 'react-hook-form';

import { useFormFieldValidation } from '#modules/form/hooks/useFormFieldValidation.ts';
import type { ValuesOfField } from '#modules/form/types.ts';
import { getFieldName } from '#modules/form/utils.ts';

interface Props {
  field: SingleSelectField;
  autoFocus?: boolean;
}

export function SingleSelectField({ field, autoFocus }: Props) {
  const id = useId();
  const { label, options } = field;

  const { register, formState } = useFormContext<ValuesOfField<SingleSelectField>>();
  const { rules, invalid, invalidText } = useFormFieldValidation({ field, formState });

  const inputProps = register(getFieldName(field), rules);

  return (
    <Select
      id={id}
      size="lg"
      labelText={label}
      invalid={invalid}
      invalidText={invalidText}
      autoFocus={autoFocus}
      {...inputProps}
    >
      {options.map(({ id, label }) => (
        <SelectItem key={id} text={label} value={id} />
      ))}
    </Select>
  );
}
