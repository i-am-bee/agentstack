/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { DatePicker, DatePickerInput } from '@carbon/react';
import type { DateField } from 'beeai-sdk';
import { Controller, useFormContext } from 'react-hook-form';

import type { ValuesOfField } from '#modules/form/types.ts';

interface Props {
  field: DateField;
}

export function DateField({ field }: Props) {
  const { id, label, placeholder } = field;

  const { control } = useFormContext<ValuesOfField<DateField>>();

  return (
    <Controller
      name={`${id}.value`}
      control={control}
      render={({ field: { value, onChange } }) => (
        <DatePicker
          datePickerType="single"
          value={value ?? undefined}
          onChange={(_, currentDateString) => onChange(currentDateString)}
          allowInput
        >
          <DatePickerInput id={id} size="lg" labelText={label} placeholder={placeholder ?? undefined} />
        </DatePicker>
      )}
    />
  );
}
