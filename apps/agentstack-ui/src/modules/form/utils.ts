/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FormField } from 'agentstack-sdk';
import keyBy from 'lodash/keyBy';
import mapValues from 'lodash/mapValues';
import { match } from 'ts-pattern';

import { getFilePlatformUrl } from '#api/a2a/utils.ts';
import type { FileEntity } from '#modules/files/types.ts';

import type { RunFormValues } from './types';

export function getDefaultValues(fields: FormField[]) {
  const defaultValues: RunFormValues = Object.fromEntries(
    fields.map((field) =>
      match(field)
        .with(
          { type: 'text' },
          { type: 'date' },
          { type: 'singleselect' },
          { type: 'multiselect' },
          { type: 'checkbox' },
          ({ id, type, default_value }) => [
            id,
            {
              type,
              value: default_value,
            },
          ],
        )
        .with({ type: 'checkbox_group' }, ({ id, type, fields }) => [
          id,
          {
            type,
            value: mapValues(
              keyBy(fields, ({ id }) => id),
              ({ default_value }) => default_value,
            ),
          },
        ])
        .otherwise(({ id, type }) => [id, { type }]),
    ),
  );

  return defaultValues;
}

export function convertFileToFileFieldValue(file: FileEntity) {
  const { uploadFile, originalFile } = file;

  if (!uploadFile) {
    return;
  }

  const { id, filename } = uploadFile;
  const { type } = originalFile;

  const value = {
    uri: getFilePlatformUrl(id),
    name: filename,
    mime_type: type,
  };

  return value;
}

export function getFieldName(field: FormField) {
  return `${field.id}.value` as const;
}
