/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { TextInput } from '@carbon/react';
import type { TextField } from 'agentstack-sdk';
import { useFormContext } from 'react-hook-form';

import { FormRequirement } from '#components/FormRequirement/FormRequirement.tsx';
import { TextAreaAutoHeight } from '#components/TextAreaAutoHeight/TextAreaAutoHeight.tsx';
import type { ValuesOfField } from '#modules/form/types.ts';

import { FormLabel } from '../FormLabel';
import { REQUIRED_ERROR_MESSAGE } from './constants';

interface Props {
  field: TextField;
}

export function TextField({ field }: Props) {
  const { id, label, placeholder, required, auto_resize } = field;

  const {
    register,
    formState: { errors },
  } = useFormContext<ValuesOfField<TextField>>();
  const error = errors[id];

  const { invalidText, ...inputProps } = {
    id,
    placeholder: placeholder ?? undefined,
    invalid: Boolean(error),
    invalidText: error?.value?.message,
    ...register(`${id}.value`, { required: Boolean(required) && REQUIRED_ERROR_MESSAGE }),
  };

  if (auto_resize) {
    return (
      <div>
        <FormLabel htmlFor={id}>{label}</FormLabel>

        <TextAreaAutoHeight className="cds--text-input__field-wrapper" size="lg" rows={1} maxRows={8} {...inputProps} />

        {inputProps.invalid && <FormRequirement>{invalidText}</FormRequirement>}
      </div>
    );
  }

  return <TextInput size="lg" labelText={label} invalidText={invalidText} {...inputProps} />;
}
