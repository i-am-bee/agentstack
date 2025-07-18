/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FilePart, FileWithUri } from '@a2a-js/sdk';
import { v4 as uuid } from 'uuid';

import type { FileEntity } from '#modules/files/types.ts';
import type { UIAgentMessage, UIFilePart, UITransformPart } from '#modules/messages/types.ts';
import { UIMessagePartKind, UITransformType } from '#modules/messages/types.ts';
import { isImageMimeType, isNotNull } from '#utils/helpers.ts';
import { toMarkdownImage } from '#utils/markdown.ts';

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

export function convertFilesToUIFileParts(files: FileEntity[]): UIFilePart[] {
  const parts: UIFilePart[] = files
    .map(({ uploadFile, originalFile: { type } }) => {
      if (!uploadFile) {
        return;
      }

      const { id, filename } = uploadFile;

      return {
        kind: UIMessagePartKind.File,
        id,
        filename,
        type,
        url: getFileContentUrl({ id }),
      } as UIFilePart;
    })
    .filter(isNotNull);

  return parts;
}

export function processFilePart(part: FilePart, message: UIAgentMessage): (UIFilePart | UITransformPart)[] {
  const { file } = part;
  const { name, mimeType } = file;
  const id = uuid();
  const url = getFileUri(file);

  const filePart: UIFilePart = {
    kind: UIMessagePartKind.File,
    url,
    id,
    filename: name || id,
    type: mimeType,
  };

  const isImage = isImageMimeType(mimeType);

  if (!isImage) {
    return [filePart];
  }

  const startIndex = message.content.length;

  const transformPart: UITransformPart = {
    kind: UIMessagePartKind.Transform,
    id: uuid(),
    type: UITransformType.Image,
    startIndex,
    apply: (content, offset) => {
      const adjustedStartIndex = startIndex + offset;
      const before = content.slice(0, adjustedStartIndex);
      const after = content.slice(adjustedStartIndex);

      return `${before}${toMarkdownImage(url)}${after}`;
    },
  };

  return [filePart, transformPart];
}
