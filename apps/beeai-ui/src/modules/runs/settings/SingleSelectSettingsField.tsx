/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { RadioButton, RadioButtonGroup } from '@carbon/react';
import { useId } from 'react';
import { useController } from 'react-hook-form';

import type { SingleSelectFieldValue } from '#api/a2a/extensions/ui/settings.ts';

export function SingleSelectSettingsField({
  field,
}: {
  field: { id: string; options: { value: string; label: string }[] };
}) {
  const htmlId = useId();
  const { id } = field;

  const {
    field: { onChange, value },
  } = useController<{ [key: string]: SingleSelectFieldValue }>({
    name: `${id}.value`,
  });

  return (
    <RadioButtonGroup
      legendText=""
      name="radio-button-vertical-group"
      valueSelected={value?.value}
      orientation="vertical"
    >
      {field.options.map(({ value, label }) => (
        <RadioButton
          key={value}
          id={`${htmlId}:${value}`}
          value={value}
          labelText={label}
          onChange={(value) => {
            onChange({ type: 'single_select', value });
          }}
        />
      ))}
    </RadioButtonGroup>
  );
  // return (
  //   <Select
  //     id={id}
  //     {...register(`${id}.value`, {
  //       onChange: onChanged,
  //     })}
  //   >
  //     {field.options.map(({ value, label }) => (
  //       <SelectItem key={value} value={value} text={label} />
  //     ))}
  //   </Select>
  // );
}
