/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { DatePicker, DatePickerInput } from '@carbon/react';
import type { DateField } from 'agentstack-sdk';
import { Controller, useFormContext } from 'react-hook-form';

import { useFormFieldValidation } from '#modules/form/hooks/useFormFieldValidation.ts';
import type { ValuesOfField } from '#modules/form/types.ts';
import { getFieldName } from '#modules/form/utils.ts';

interface Props {
  field: DateField;
}

export function DateField({ field }: Props) {
  const { id, label, placeholder } = field;

  const { control, formState } = useFormContext<ValuesOfField<DateField>>();
  const { rules, invalid, invalidText } = useFormFieldValidation({ field, formState });

  return (
    <Controller
      name={getFieldName(field)}
      control={control}
      rules={rules}
      render={({ field: { value, onChange } }) => (
        <DatePicker
          datePickerType="single"
          value={value ?? undefined}
          onChange={(_, currentDateString) => onChange(currentDateString)}
          allowInput
          invalid={invalid}
        >
          <DatePickerInput
            id={id}
            size="lg"
            labelText={label}
            placeholder={placeholder ?? undefined}
            invalidText={invalidText}
          />
        </DatePicker>
      )}
    />
  );
}
