/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CloudUpload } from '@carbon/icons-react';
import clsx from 'clsx';

import { useApp } from '#contexts/App/index.ts';

import classes from './FileUploadDropzone.module.scss';

export function FileUploadDropzone() {
  const { sidebarOpen } = useApp();

  return (
    <div className={clsx(classes.root, { [classes.sidebarOpen]: sidebarOpen })}>
      <div className={classes.content}>
        <CloudUpload size={96} />

        <h2 className={classes.heading}>Drag & Drop</h2>

        <p className={classes.description}>Drop to add file to current session</p>
      </div>
    </div>
  );
}
