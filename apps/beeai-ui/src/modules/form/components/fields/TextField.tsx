/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { TextInput } from '@carbon/react';
import type { TextField } from 'agentstack-sdk';
import { useFormContext } from 'react-hook-form';

import { TextAreaAutoHeight } from '#components/TextAreaAutoHeight/TextAreaAutoHeight.tsx';
import type { ValuesOfField } from '#modules/form/types.ts';

import { FormLabel } from '../FormLabel';

interface Props {
  field: TextField;
}

export function TextField({ field }: Props) {
  const { id, label, placeholder, required, auto_resize } = field;

  const { register } = useFormContext<ValuesOfField<TextField>>();

  const inputProps = register(`${id}.value`, { required: Boolean(required) });

  if (auto_resize) {
    return (
      <div>
        <FormLabel htmlFor={id}>{label}</FormLabel>

        <TextAreaAutoHeight
          id={id}
          size="lg"
          rows={1}
          placeholder={placeholder ?? undefined}
          maxRows={8}
          {...inputProps}
        />
      </div>
    );
  }

  return <TextInput id={id} size="lg" labelText={label} placeholder={placeholder ?? undefined} {...inputProps} />;
}
