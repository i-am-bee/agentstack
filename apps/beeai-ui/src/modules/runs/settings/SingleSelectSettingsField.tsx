/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Checkmark } from '@carbon/icons-react';
import { RadioButton, RadioButtonGroup } from '@carbon/react';
import clsx from 'clsx';
import { useId } from 'react';
import { useController } from 'react-hook-form';

import type { SingleSelectFieldValue } from '#api/a2a/extensions/ui/settings.ts';

import classes from './SingleSelectSettingsField.module.scss';

export function SingleSelectSettingsField({
  field,
}: {
  field: { id: string; options: { value: string; label: string }[] };
}) {
  const htmlId = useId();
  const { id } = field;

  const {
    field: { onChange, value },
  } = useController<{ [key: string]: SingleSelectFieldValue }, `${typeof id}.value`>({
    name: `${id}.value`,
  });

  return (
    <RadioButtonGroup
      legendText=""
      name="radio-button-vertical-group"
      valueSelected={value}
      orientation="vertical"
      className={classes.root}
    >
      {field.options.map(({ value: optionValue, label }) => {
        const isSelected = optionValue === value;
        return (
          <div className={clsx(classes.option, { [classes.selected]: isSelected })} key={optionValue}>
            <RadioButton
              id={`${htmlId}:${optionValue}`}
              value={optionValue}
              labelText={label}
              onClick={() => onChange(optionValue)}
            />
            {optionValue === value && <Checkmark size={16} />}
          </div>
        );
      })}
    </RadioButtonGroup>
  );
}
