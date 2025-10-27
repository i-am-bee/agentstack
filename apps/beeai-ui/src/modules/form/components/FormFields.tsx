/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FormDemands, FormFullfillments } from 'beeai-sdk';
import type { CSSProperties } from 'react';

import { FormField } from './FormField';
import classes from './FormFields.module.scss';

interface Props {
  fields: FormDemands['fields'];
  columns: FormDemands['columns'];
  values?: FormFullfillments['values'];
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
