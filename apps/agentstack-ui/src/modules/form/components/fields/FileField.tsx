/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Add } from '@carbon/icons-react';
import { Button, FormGroup } from '@carbon/react';
import type { FileField } from 'agentstack-sdk';
import { useEffect } from 'react';
import { useController, useFormContext } from 'react-hook-form';

import { FormRequirement } from '#components/FormRequirement/FormRequirement.tsx';
import { usePrevious } from '#hooks/usePrevious.ts';
import { FileCard } from '#modules/files/components/FileCard.tsx';
import { FileCardsList } from '#modules/files/components/FileCardsList.tsx';
import { FileUploadProvider } from '#modules/files/contexts/FileUploadProvider.tsx';
import { useFileUpload } from '#modules/files/contexts/index.ts';
import { useFormFieldValidation } from '#modules/form/hooks/useFormFieldValidation.ts';
import type { ValuesOfField } from '#modules/form/types.ts';
import { convertFileToFileFieldValue, getFieldName } from '#modules/form/utils.ts';
import { isNotNull } from '#utils/helpers.ts';

import classes from './FileField.module.scss';

interface Props {
  field: FileField;
  autoFocus?: boolean;
}

export function FileField({ field, autoFocus }: Props) {
  return (
    <FileUploadProvider allowedContentTypes={field.accept}>
      <FileFieldComponent field={field} autoFocus={autoFocus} />
    </FileUploadProvider>
  );
}

export function FileFieldComponent({ field, autoFocus }: Props) {
  const { label } = field;

  const { dropzone, isDisabled, isPending, files, removeFile } = useFileUpload();
  const { control, formState } = useFormContext<ValuesOfField<FileField>>();
  const { rules, invalid: invalidState, invalidText } = useFormFieldValidation({ field, formState });
  const {
    field: { onChange },
  } = useController({ control, name: getFieldName(field), rules });

  const invalid = invalidState && !isPending;

  const hasFiles = files.length > 0;
  const filesKey = files
    .map(({ uploadFile }) => (uploadFile ? uploadFile.id : null))
    .filter(isNotNull)
    .join('|');
  const prevFilesKey = usePrevious(filesKey);

  useEffect(() => {
    if (prevFilesKey === filesKey) {
      return;
    }

    const newValue = files.map(convertFileToFileFieldValue).filter(isNotNull);

    onChange(newValue);
  }, [filesKey, prevFilesKey, files, onChange]);

  if (!dropzone) {
    return null;
  }

  return (
    <FormGroup {...dropzone.getRootProps()} legendText={label}>
      <input type="file" {...dropzone.getInputProps()} data-invalid={invalid} />

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
          autoFocus={autoFocus}
        >
          Upload
        </Button>
      )}

      {invalid && <FormRequirement>{invalidText}</FormRequirement>}
    </FormGroup>
  );
}
