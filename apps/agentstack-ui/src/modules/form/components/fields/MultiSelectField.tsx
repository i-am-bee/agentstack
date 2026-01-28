/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { FormGroup, OperationalTag } from '@carbon/react';
import type { MultiSelectField } from 'agentstack-sdk';
import clsx from 'clsx';
import { useCallback } from 'react';
import { Controller, useFormContext } from 'react-hook-form';

import { FormRequirement } from '#components/FormRequirement/FormRequirement.tsx';
import { useFormFieldValidation } from '#modules/form/hooks/useFormFieldValidation.ts';
import type { ValuesOfField } from '#modules/form/types.ts';
import { getFieldName } from '#modules/form/utils.ts';

import classes from './MultiSelect.module.scss';

interface Props {
  field: MultiSelectField;
}

export function MultiSelectField({ field }: Props) {
  const { label, options } = field;

  const { control, formState } = useFormContext<ValuesOfField<MultiSelectField>>();
  const { rules, invalid, invalidText } = useFormFieldValidation({ field, formState });

  const toggle = useCallback(
    ({ value, id, onChange }: { value: string[]; id: string; onChange: (value: string[]) => void }) => {
      const isSelected = value.includes(id);
      const newValue = isSelected ? value.filter((item) => item !== id) : [...value, id];

      onChange(newValue);
    },
    [],
  );

  return (
    <FormGroup legendText={label}>
      <Controller
        name={getFieldName(field)}
        control={control}
        rules={rules}
        render={({ field: { value, onChange } }) => (
          <ul className={clsx(classes.root, 'cds--text-input__field-wrapper')} data-invalid={invalid}>
            {options.map(({ id, label }) => {
              const isSelected = value?.includes(id);

              return (
                <li key={id}>
                  <OperationalTag
                    text={label}
                    size="lg"
                    className={clsx(classes.option, { ['cds--tag--selected']: isSelected })}
                    onClick={() => toggle({ value: value ?? [], id, onChange })}
                  />
                </li>
              );
            })}
          </ul>
        )}
      />

      {invalid && <FormRequirement>{invalidText}</FormRequirement>}
    </FormGroup>
  );
}
