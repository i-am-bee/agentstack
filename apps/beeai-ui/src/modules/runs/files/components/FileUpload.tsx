/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import { useFileUpload } from '../contexts';
import classes from './FileUpload.module.scss';
import { FileUploadDropzone } from './FileUploadDropzone';

export function FileUpload({ children }: PropsWithChildren) {
  const { dropzone } = useFileUpload();

  const dropzoneProps = dropzone ? dropzone.getRootProps() : {};

  return (
    <div className={classes.root} {...dropzoneProps}>
      {children}

      {dropzone?.isDragActive && <FileUploadDropzone />}
    </div>
  );
}
