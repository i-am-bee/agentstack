/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FilePart, Message } from '@a2a-js/sdk';
import { v4 as uuid } from 'uuid';

import type { FileEntity } from '#modules/files/types.ts';
import { getFileContentUrl } from '#modules/files/utils.ts';

export function convertFileToFilePart(file: FileEntity): FilePart {
  const { originalFile, uploadFile } = file;

  if (!uploadFile) {
    throw new Error('File upload file is not present');
  }

  return {
    kind: 'file',
    file: {
      uri: getFileContentUrl({ id: uploadFile.id, addBase: true }),
      name: uploadFile.filename,
      mimeType: originalFile.type,
    },
  };
}

export function createUserMessage(message: string, files: FileEntity[], contextId: string, taskId: string): Message {
  return {
    kind: 'message',
    messageId: uuid(),
    contextId,
    taskId,
    parts: [
      {
        kind: 'text',
        text: message,
      },
      ...files.map(convertFileToFilePart),
    ],
    role: 'user',
  };
}
