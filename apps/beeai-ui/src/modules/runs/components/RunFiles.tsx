/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { FileCard } from '#modules/files/components/FileCard.tsx';
import { FileCardsList } from '#modules/files/components/FileCardsList.tsx';
import { useFileUpload } from '#modules/files/contexts/index.ts';

import classes from './RunFiles.module.scss';

export function RunFiles() {
  const { files, removeFile } = useFileUpload();

  const hasFiles = files.length > 0;

  if (!hasFiles) {
    return null;
  }

  return (
    <div className={classes.root}>
      <FileCardsList>
        {files.map(({ id, originalFile: { name }, status }) => (
          <li key={id}>
            <FileCard size="sm" filename={name} status={status} onRemoveClick={() => removeFile(id)} />
          </li>
        ))}
      </FileCardsList>
    </div>
  );
}
