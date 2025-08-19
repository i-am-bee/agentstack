/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
import { v4 as uuid } from 'uuid';

import type { FileEntity } from '#modules/files/types.ts';
import type { UIAgentMessage, UIFilePart, UITransformPart } from '#modules/messages/types.ts';
import { UIMessagePartKind, UITransformType } from '#modules/messages/types.ts';
import { getMessageRawContent } from '#modules/messages/utils.ts';
import { isImageMimeType, isNotNull } from '#utils/helpers.ts';
import { toMarkdownImage } from '#utils/markdown.ts';

import { FILE_CONTENT_URL } from './constants';

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

export function getFileContentUrl(id: string) {
  return FILE_CONTENT_URL.replace('{file_id}', id);
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
        url: getFileContentUrl(id),
      } as UIFilePart;
    })
    .filter(isNotNull);

  return parts;
}

export function transformFilePart(filePart: UIFilePart, message: UIAgentMessage): UITransformPart | null {
  const { url, type } = filePart;
  const isImage = isImageMimeType(type);

  if (!isImage) {
    return null;
  }

  const startIndex = getMessageRawContent(message).length;

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

  return transformPart;
}
