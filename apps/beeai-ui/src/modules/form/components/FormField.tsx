/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FormField, FormResponseValue } from 'agentstack-sdk';
import type { CSSProperties } from 'react';
import { match, P } from 'ts-pattern';

import { CheckboxField } from './fields/CheckboxField';
import { DateField } from './fields/DateField';
import { FileField } from './fields/FileField';
import { FileFieldValue } from './fields/FileFieldValue';
import { MultiSelectField } from './fields/MultiSelectField';
import { SingleSelectField } from './fields/SingleSelectField';
import { TextField } from './fields/TextField';
import classes from './FormField.module.scss';

interface Props {
  field: FormField;
  value?: FormResponseValue;
}

export function FormField({ field, value }: Props) {
  const { col_span } = field;

  const component = match(field)
    .with({ type: 'text' }, (field) => <TextField field={field} />)
    .with({ type: 'date' }, (field) => <DateField field={field} />)
    .with({ type: 'file' }, (field) =>
      match(value)
        .with({ type: 'file', value: P.nonNullable }, ({ value }) => <FileFieldValue field={field} value={value} />)
        .otherwise(() => <FileField field={field} />),
    )
    .with({ type: 'singleselect' }, (field) => <SingleSelectField field={field} />)
    .with({ type: 'multiselect' }, (field) => <MultiSelectField field={field} />)
    .with({ type: 'checkbox' }, (field) => <CheckboxField field={field} />)
    .exhaustive();

  return (
    <div className={classes.root} style={{ '--col-span': col_span } as CSSProperties}>
      {component}
    </div>
  );
}
