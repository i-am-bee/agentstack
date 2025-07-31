/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FilePart, TextPart } from '@a2a-js/sdk';
import { v4 as uuid } from 'uuid';

import type { UIFilePart, UIMessagePart } from '#modules/messages/types.ts';
import { UIMessagePartKind } from '#modules/messages/types.ts';

import {
  createSourcePart,
  createTextPart,
  createTrajectoryPart,
  extractCitation,
  extractTrajectory,
  getFileUri,
} from './utils';

export function processTextPart(part: TextPart, messageId: string): UIMessagePart[] {
  const parts: UIMessagePart[] = [];
  const { metadata, text } = part;
  const trajectory = extractTrajectory(metadata);
  const citation = extractCitation(metadata);

  if (trajectory) {
    parts.push(createTrajectoryPart(trajectory));
  } else if (citation) {
    const sourcePart = createSourcePart(citation, messageId);

    if (sourcePart) {
      parts.push(sourcePart);
    }
  }

  parts.push(createTextPart(text));

  return parts;
}

export function processFilePart(part: FilePart): UIMessagePart[] {
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

  return [filePart];
}
