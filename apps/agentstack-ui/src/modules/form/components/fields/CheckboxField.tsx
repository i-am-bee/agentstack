/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Checkbox, FormGroup } from '@carbon/react';
import type { CheckboxField } from 'agentstack-sdk';
import { useFormContext } from 'react-hook-form';

import { useFormFieldValidation } from '#modules/form/hooks/useFormFieldValidation.ts';
import type { ValuesOfField } from '#modules/form/types.ts';
import { getFieldName } from '#modules/form/utils.ts';

interface Props {
  field: CheckboxField;
}

export function CheckboxField({ field }: Props) {
  const { id, label, content } = field;

  const { register, formState } = useFormContext<ValuesOfField<CheckboxField>>();
  const { rules, invalid, invalidText } = useFormFieldValidation({ field, formState });

  const inputProps = register(getFieldName(field), rules);

  return (
    <FormGroup legendText={label}>
      <Checkbox id={id} labelText={content} invalid={invalid} invalidText={invalidText} {...inputProps} />
    </FormGroup>
  );
}
