/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Checkbox, FormGroup } from '@carbon/react';
import { useFormContext } from 'react-hook-form';

import type { CheckboxField } from '#api/a2a/extensions/ui/form.ts';
import type { ValuesOfField } from '#modules/form/types.ts';

interface Props {
  field: CheckboxField;
}

export function CheckboxField({ field }: Props) {
  const { id, label, content, required } = field;

  const { register } = useFormContext<ValuesOfField<CheckboxField>>();

  return (
    <FormGroup legendText={label}>
      <Checkbox id={id} labelText={content} {...register(`${id}.value`, { required: Boolean(required) })} />
    </FormGroup>
  );
}
