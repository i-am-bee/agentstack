/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CheckboxGroup } from '@carbon/react';
import type { CheckboxGroupField, CheckboxGroupFieldValue } from 'agentstack-sdk';
import { useController, useFormContext } from 'react-hook-form';

import { REQUIRED_GROUP_ERROR_MESSAGE } from '#modules/form/constants.ts';
import { useFormFieldValidation } from '#modules/form/hooks/useFormFieldValidation.ts';
import type { ValuesOfField } from '#modules/form/types.ts';
import { getFieldName } from '#modules/form/utils.ts';

import classes from './CheckboxGroupField.module.scss';
import { CheckboxGroupFieldItem } from './CheckboxGroupFieldItem';

interface Props {
  field: CheckboxGroupField;
  autoFocus?: boolean;
}

export function CheckboxGroupField({ field, autoFocus }: Props) {
  const { label, fields, required } = field;
  const name = getFieldName(field);

  const { control, formState } = useFormContext<ValuesOfField<CheckboxGroupField>>();
  const {
    rules,
    invalid: invalidState,
    invalidText,
  } = useFormFieldValidation({
    field,
    formState,
    rules: {
      validate: (value: CheckboxGroupFieldValue['value']) => {
        if (!required) {
          return true;
        }

        return Object.values(value ?? {}).some(Boolean) || REQUIRED_GROUP_ERROR_MESSAGE;
      },
    },
  });
  const invalid = invalidState && Boolean(invalidText);

  useController({ control, name, rules });

  return (
    <CheckboxGroup className={classes.root} legendText={label} invalid={invalid} invalidText={invalidText}>
      {fields.map((itemField, index) => (
        <CheckboxGroupFieldItem
          key={itemField.id}
          field={itemField}
          groupField={field}
          autoFocus={autoFocus && index === 0}
        />
      ))}
    </CheckboxGroup>
  );
}
