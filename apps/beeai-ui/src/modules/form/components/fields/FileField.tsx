/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Add } from '@carbon/icons-react';
import { Button, FormGroup } from '@carbon/react';
import type { FileField } from 'beeai-sdk';
import { useEffect } from 'react';
import { useController, useFormContext } from 'react-hook-form';

import { FileCard } from '#modules/files/components/FileCard.tsx';
import { FileCardsList } from '#modules/files/components/FileCardsList.tsx';
import { FileUploadProvider } from '#modules/files/contexts/FileUploadProvider.tsx';
import { useFileUpload } from '#modules/files/contexts/index.ts';
import type { ValuesOfField } from '#modules/form/types.ts';
import { convertFileToFileFieldValue } from '#modules/form/utils.ts';
import { isNotNull } from '#utils/helpers.ts';

import classes from './FileField.module.scss';

interface Props {
  field: FileField;
}

export function FileField({ field }: Props) {
  return (
    <FileUploadProvider allowedContentTypes={field.accept}>
      <FileFieldComponent field={field} />
    </FileUploadProvider>
  );
}

export function FileFieldComponent({ field }: Props) {
  const { id, label } = field;

  const { dropzone, isDisabled, files, removeFile } = useFileUpload();
  const { control } = useFormContext<ValuesOfField<FileField>>();
  const {
    field: { onChange },
  } = useController({ control, name: `${id}.value` });

  const hasFiles = files.length > 0;

  useEffect(() => {
    const newValue = files.map(convertFileToFileFieldValue).filter(isNotNull);

    onChange(newValue);
  }, [files, onChange]);

  if (!dropzone) {
    return null;
  }

  return (
    <FormGroup {...dropzone.getRootProps()} legendText={label} className={classes.root}>
      <input type="file" {...dropzone.getInputProps()} />

      {hasFiles ? (
        <FileCardsList className={classes.files}>
          {files.map(({ id, originalFile: { name }, status }) => (
            <li key={id}>
              <FileCard size="sm" filename={name} status={status} onRemoveClick={() => removeFile(id)} />
            </li>
          ))}
        </FileCardsList>
      ) : (
        <Button
          onClick={dropzone.open}
          kind="tertiary"
          size="lg"
          renderIcon={Add}
          className={classes.button}
          disabled={isDisabled}
        >
          Upload
        </Button>
      )}
    </FormGroup>
  );
}
