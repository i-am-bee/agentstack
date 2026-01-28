/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { TextInput } from '@carbon/react';
import type { TextField } from 'agentstack-sdk';
import { useFormContext } from 'react-hook-form';

import { FormRequirement } from '#components/FormRequirement/FormRequirement.tsx';
import { TextAreaAutoHeight } from '#components/TextAreaAutoHeight/TextAreaAutoHeight.tsx';
import { useFormFieldValidation } from '#modules/form/hooks/useFormFieldValidation.ts';
import type { ValuesOfField } from '#modules/form/types.ts';
import { getFieldName } from '#modules/form/utils.ts';

import { FormLabel } from '../FormLabel';

interface Props {
  field: TextField;
}

export function TextField({ field }: Props) {
  const { id, label, placeholder, auto_resize } = field;

  const { register, formState } = useFormContext<ValuesOfField<TextField>>();
  const { rules, invalid, invalidText } = useFormFieldValidation({ field, formState });

  const inputProps = {
    id,
    placeholder: placeholder ?? undefined,
    ...register(getFieldName(field), rules),
  };

  if (auto_resize) {
    return (
      <div>
        <FormLabel htmlFor={id}>{label}</FormLabel>

        <TextAreaAutoHeight
          className="cds--text-input__field-wrapper"
          size="lg"
          rows={1}
          maxRows={8}
          invalid={invalid}
          {...inputProps}
        />

        {invalid && <FormRequirement>{invalidText}</FormRequirement>}
      </div>
    );
  }

  return <TextInput size="lg" labelText={label} invalid={invalid} invalidText={invalidText} {...inputProps} />;
}
