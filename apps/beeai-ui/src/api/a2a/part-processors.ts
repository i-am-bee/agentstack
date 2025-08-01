/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FilePart, Message, TextPart } from '@a2a-js/sdk';
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

export function processMessageMetadata(message: Message): UIMessagePart[] {
  const trajectory = extractTrajectory(message.metadata);
  const citation = extractCitation(message.metadata);

  if (trajectory) {
    return [createTrajectoryPart(trajectory)];
  } else if (citation) {
    const sourcePart = createSourcePart(citation, message.messageId);

    if (sourcePart) {
      return [sourcePart];
    }
  }

  return [];
}

export function processTextPart({ text }: TextPart): UIMessagePart[] {
  return [createTextPart(text)];
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
