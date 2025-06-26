/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { v4 as uuid } from 'uuid';

import type { Artifact } from '../api/types';
import type { MessageFile } from '../chat/types';
import { FILE_CONTENT_URL, FILE_CONTENT_URL_BASE } from './constants';

export function parseFilename(filename: string) {
  const lastDotIndex = filename.lastIndexOf('.');

  if (lastDotIndex === -1) {
    return {
      name: filename,
      ext: '',
    };
  }

  return {
    name: filename.slice(0, lastDotIndex),
    ext: filename.slice(lastDotIndex + 1),
  };
}

export function getFileContentUrl({ id, addBase }: { id: string; addBase?: boolean }) {
  return `${addBase ? FILE_CONTENT_URL_BASE : ''}${FILE_CONTENT_URL.replace('{file_id}', id)}`;
}

export function prepareMessageFiles({ files = [], data }: { files: MessageFile[] | undefined; data: Artifact }) {
  const { name, content_url } = data;

  const newFiles: MessageFile[] = content_url
    ? [
        ...files,
        {
          key: uuid(),
          filename: name,
          href: content_url,
        },
      ]
    : files;

  return newFiles;
}
