/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { SingleSelectField, SingleSelectFieldValue } from 'agentstack-sdk';
import { useController } from 'react-hook-form';

import { RadioSelect } from '#components/RadioSelect/RadioSelect.tsx';
import { getFieldName } from '#modules/form/utils.ts';

interface Props {
  field: SingleSelectField;
}

export function SingleSelectSettingsField({ field }: Props) {
  const { label } = field;

  const name = getFieldName(field);
  const options = field.options.map(({ id, label }) => ({ value: id, label }));

  const {
    field: { value, onChange },
  } = useController<Record<string, SingleSelectFieldValue>, typeof name>({ name });

  return (
    <RadioSelect
      name="radio-button-vertical-group"
      label={label}
      value={value ?? undefined}
      options={options}
      onChange={onChange}
    />
  );
}
