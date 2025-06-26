/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Attachment } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';

import { useFileUpload } from '../contexts';
import classes from './FileUploadButton.module.scss';

export function FileUploadButton() {
  const { dropzone } = useFileUpload();

  if (!dropzone) {
    return null;
  }

  return (
    <>
      <input type="file" {...dropzone.getInputProps()} />

      <IconButton onClick={dropzone.open} label="File upload" kind="ghost" size="sm" wrapperClasses={classes.root}>
        <Attachment />
      </IconButton>
    </>
  );
}
