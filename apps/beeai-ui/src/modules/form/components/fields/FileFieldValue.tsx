/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FileField, FormResponseValue } from 'beeai-sdk';
import { FormGroup } from '@carbon/react';

import { getFileIdFromFilePlatformUrl } from '#api/a2a/utils.ts';
import { FileCard } from '#modules/files/components/FileCard.tsx';
import { FileCardsList } from '#modules/files/components/FileCardsList.tsx';
import { getFileContentUrl } from '#modules/files/utils.ts';

import classes from './FielFieldValue.module.scss';

interface Props {
  field: FileField;
  value: NonNullable<Extract<FormResponseValue, { type: 'file' }>['value']>;
}

export function FileFieldValue({ field, value }: Props) {
  const { label } = field;
  const hasFiles = value.length > 0;

  return (
    <FormGroup legendText={label}>
      {hasFiles ? (
        <FileCardsList className={classes.files}>
          {value.map(({ uri, name }) => {
            const href = getFileContentUrl(getFileIdFromFilePlatformUrl(uri));
            const filename = name ?? uri;

            return (
              <li key={uri}>
                <FileCard href={href} size="sm" filename={filename} />
              </li>
            );
          })}
        </FileCardsList>
      ) : (
        <p className={classes.empty}>No files selected</p>
      )}
    </FormGroup>
  );
}
