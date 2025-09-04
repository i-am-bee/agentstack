/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { FormGroup, OperationalTag } from '@carbon/react';
import clsx from 'clsx';
import { useCallback } from 'react';
import { Controller, useFormContext } from 'react-hook-form';

import type { MultiSelectField } from '#api/a2a/extensions/ui/form.ts';
import type { ValuesOfField } from '#modules/form/types.ts';

import classes from './MultiSelect.module.scss';

interface Props {
  field: MultiSelectField;
}

export function MultiSelectField({ field }: Props) {
  const { id, label, options } = field;

  const { control } = useFormContext<ValuesOfField<MultiSelectField>>();

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
        name={`${id}.value`}
        control={control}
        render={({ field: { value, onChange } }) => (
          <ul className={classes.root}>
            {options.map(({ id, label }) => {
              const isSelected = value?.includes(id);

              return (
                <li key={id}>
                  <OperationalTag
                    text={label}
                    size="lg"
                    className={clsx(classes.option, { [classes.isSelected]: isSelected })}
                    onClick={() => toggle({ value: value ?? [], id, onChange })}
                  />
                </li>
              );
            })}
          </ul>
        )}
      />
    </FormGroup>
  );
}
