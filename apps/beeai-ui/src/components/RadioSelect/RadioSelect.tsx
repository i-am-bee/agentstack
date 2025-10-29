/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Checkmark } from '@carbon/icons-react';
import { RadioButton, RadioButtonGroup } from '@carbon/react';
import clsx from 'clsx';
import { useId } from 'react';

import classes from './RadioSelect.module.scss';

interface Props {
  name: string;
  label: string;
  value?: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
}

export function RadioSelect({ name, label, value, options, onChange }: Props) {
  const htmlId = useId();

  return (
    <RadioButtonGroup
      legendText={label}
      name={name}
      valueSelected={value}
      orientation="vertical"
      className={classes.root}
    >
      {options.map(({ value: optionValue, label }) => {
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
