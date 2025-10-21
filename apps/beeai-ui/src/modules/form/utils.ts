/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FormField } from 'beeai-sdk';
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
          ({ id, type, default_value }) => [id, { type, value: default_value }],
        )
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

export function getNormalizedField(field: FormField) {
  return {
    ...field,
  };
}
