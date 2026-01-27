/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { DatePicker, DatePickerInput } from '@carbon/react';
import type { DateField } from 'agentstack-sdk';
import { Controller, useFormContext } from 'react-hook-form';

import type { ValuesOfField } from '#modules/form/types.ts';

import { REQUIRED_ERROR_MESSAGE } from './constants';

interface Props {
  field: DateField;
}

export function DateField({ field }: Props) {
  const { id, label, placeholder, required } = field;

  const {
    control,
    formState: { errors },
  } = useFormContext<ValuesOfField<DateField>>();
  const error = errors[id];

  return (
    <Controller
      name={`${id}.value`}
      control={control}
      rules={{ required: Boolean(required) && REQUIRED_ERROR_MESSAGE }}
      render={({ field: { value, onChange } }) => (
        <DatePicker
          datePickerType="single"
          value={value ?? undefined}
          onChange={(_, currentDateString) => onChange(currentDateString)}
          allowInput
          invalid={Boolean(error)}
        >
          <DatePickerInput
            id={id}
            size="lg"
            labelText={label}
            placeholder={placeholder ?? undefined}
            invalidText={error?.value?.message}
          />
        </DatePicker>
      )}
    />
  );
}
