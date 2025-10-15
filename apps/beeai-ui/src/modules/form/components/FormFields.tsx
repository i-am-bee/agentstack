/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FormRender, FormResponse } from 'beeai-sdk';
import type { CSSProperties } from 'react';

import { FormField } from './FormField';
import classes from './FormFields.module.scss';

interface Props {
  fields: FormRender['fields'];
  columns: FormRender['columns'];
  values?: FormResponse['values'];
}

export function FormFields({ fields, columns, values }: Props) {
  return (
    <div className={classes.root} style={{ '--grid-columns': columns } as CSSProperties}>
      {fields.map((field) => {
        return <FormField key={field.id} field={field} value={values?.[field.id]} />;
      })}
    </div>
  );
}
