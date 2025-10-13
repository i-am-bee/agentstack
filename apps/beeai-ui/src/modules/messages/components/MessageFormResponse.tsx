/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { CheckboxField, DateField, FileField, FormField, MultiSelectField, TextField } from 'beeai-sdk';
import { useMemo } from 'react';
import { match } from 'ts-pattern';

import { getFileUrl } from '#api/a2a/utils.ts';
import { FileCard } from '#modules/files/components/FileCard.tsx';
import type { ValueOfField } from '#modules/form/types.ts';
import { isNotNull } from '#utils/helpers.ts';

import type { UIMessageForm } from '../types';
import classes from './MessageFormResponse.module.scss';

interface Props {
  form: UIMessageForm;
}

export function MessageFormResponse({ form }: Props) {
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

  return (
    <>
      {data.map((field) => {
        const { id, label, value } = field;

        return value ? (
          <p key={id}>
            {label}: <FormValueRenderer field={field} />
          </p>
        ) : null;
      })}
    </>
  );
}

function FormValueRenderer({ field }: { field: FieldWithValue }) {
  return (
    <>
      {match(field)
        .with({ type: 'text' }, { type: 'date' }, ({ value }) => value)
        .with({ type: 'checkbox' }, ({ value, content }) => (value ? (content ?? 'yes') : 'no'))
        .with({ type: 'multiselect' }, ({ value }) => value?.join(', '))
        .with({ type: 'file' }, ({ value }) =>
          value?.map((file, idx) => (
            <FileCard key={`${idx}${file.uri}`} href={getFileUrl(file)} filename={file.name ?? ''} size="sm" />
          )),
        )
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
