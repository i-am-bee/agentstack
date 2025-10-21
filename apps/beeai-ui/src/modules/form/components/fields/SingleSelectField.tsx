/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Select, SelectItem } from '@carbon/react';
import type { SingleSelectField } from 'beeai-sdk';
import { useFormContext } from 'react-hook-form';

import type { ValuesOfField } from '#modules/form/types.ts';

interface Props {
  field: SingleSelectField;
}

export function SingleSelectField({ field }: Props) {
  const { id, label, required, options } = field;

  const { register } = useFormContext<ValuesOfField<SingleSelectField>>();

  const inputProps = register(`${id}.value`, { required: Boolean(required) });

  return (
    <Select id={id} size="lg" labelText={label} {...inputProps}>
      {options.map(({ id, label }) => (
        <SelectItem key={id} text={label} value={id} />
      ))}
    </Select>
  );
}
