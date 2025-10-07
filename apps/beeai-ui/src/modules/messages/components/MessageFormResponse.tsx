/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from '@carbon/react';
import { useMemo } from 'react';
import { FormProvider, useForm } from 'react-hook-form';
import { match } from 'ts-pattern';

import type {
  CheckboxField,
  DateField,
  FileField,
  FormField,
  MultiSelectField,
  TextField,
} from '#api/a2a/extensions/ui/form.ts';
import { FormFields } from '#modules/form/components/FormFields.tsx';
import { useMessageForm } from '#modules/form/contexts/index.ts';
import type { RunFormValues, ValueOfField } from '#modules/form/types.ts';
import { isNotNull } from '#utils/helpers.ts';

import type { UIMessageForm } from '../types';
import classes from './MessageFormResponse.module.scss';

interface Props {
  form: UIMessageForm;
}

export function MessageFormResponse({ form }: Props) {
  const { showSubmission, setShowSubmission } = useMessageForm();
  const formReturn = useForm<RunFormValues>({ values: form.response?.values });

  const data: FieldWithValue[] | null = useMemo(() => {
    if (!form.response) {
      return null;
    }
    return form.request.fields
      .map((field) => {
        const value = form.response?.values[field.id];
        return value && value.type === field.type ? ({ ...field, value: value.value } as FieldWithValue) : null;
      })
      .filter(isNotNull);
  }, [form.request.fields, form.response]);

  // TODO: Temporary solution for cancelled form request
  if (!data) {
    return <p className={classes.empty}>Message has no content</p>;
  }

  const { fields, columns } = form.request;

  return (
    <div className={classes.root}>
      <div>
        {data.map((field) => {
          const { id, label, value } = field;

          return value ? (
            <p key={id}>
              {label}: <FormValueRenderer field={field} />
            </p>
          ) : null;
        })}
      </div>

      {showSubmission && (
        <FormProvider {...formReturn}>
          <fieldset className={classes.submission} disabled>
            <FormFields fields={fields} columns={columns} values={form.response?.values} />
          </fieldset>
        </FormProvider>
      )}

      <Button kind="ghost" className={classes.toggleButton} onClick={() => setShowSubmission((state) => !state)}>
        {showSubmission ? 'Hide' : 'Show'} my submission
      </Button>
    </div>
  );
}

function FormValueRenderer({ field }: { field: FieldWithValue }) {
  return (
    <>
      {match(field)
        .with({ type: 'text' }, { type: 'date' }, ({ value }) => value)
        .with({ type: 'checkbox' }, ({ value }) => (value ? 'yes' : 'no'))
        .with({ type: 'multiselect' }, ({ value }) => value?.join(', '))
        .with({ type: 'file' }, ({ value }) => value?.map(({ name }) => name).join(', '))
        .otherwise(() => null)}
    </>
  );
}

type FieldWithValueMapper<F extends FormField> = F & { value: ValueOfField<F>['value'] };
type FieldWithValue =
  | FieldWithValueMapper<TextField>
  | FieldWithValueMapper<DateField>
  | FieldWithValueMapper<CheckboxField>
  | FieldWithValueMapper<MultiSelectField>
  | FieldWithValueMapper<FileField>;
