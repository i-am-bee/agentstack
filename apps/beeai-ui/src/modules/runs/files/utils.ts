/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { FilePart, FileWithUri } from '@a2a-js/sdk';
import { v4 as uuid } from 'uuid';

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

export function prepareMessageFiles({
  files = [],
  file,
}: {
  files: MessageFile[] | undefined;
  file: FilePart['file'];
}) {
  const key = uuid();
  const { name } = file;

  const newFiles: MessageFile[] = [
    ...files,
    {
      key,
      filename: name || key,
      href: getFileUri(file),
    },
  ];

  return newFiles;
}

export function isFileWithUri(file: FilePart['file']): file is FileWithUri {
  return 'uri' in file;
}

export function getFileUri(file: FilePart['file']): string {
  const isUriFile = isFileWithUri(file);

  if (isUriFile) {
    return file.uri;
  }

  const { mimeType = 'text/plain', bytes } = file;

  return `data:${mimeType};base64,${bytes}`;
}
