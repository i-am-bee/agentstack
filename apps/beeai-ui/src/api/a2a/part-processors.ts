/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FilePart, TextPart } from '@a2a-js/sdk';
import { v4 as uuid } from 'uuid';

import type { UIFilePart, UISourcePart, UITextPart, UITrajectoryPart } from '#modules/messages/types.ts';
import { UIMessagePartKind } from '#modules/messages/types.ts';

import {
  createSourcePart,
  createTextPart,
  createTrajectoryPart,
  extractCitation,
  extractTrajectory,
  getFileUri,
} from './utils';

export function processTextPart(
  part: TextPart,
  messageId: string,
): UITrajectoryPart | UISourcePart | UITextPart | null {
  const { metadata, text } = part;

  const trajectory = extractTrajectory(metadata);

  if (trajectory) {
    const trajectoryPart = createTrajectoryPart(trajectory);

    return trajectoryPart;
  }

  const citation = extractCitation(metadata);

  if (citation) {
    if (text !== '') {
      throw new Error('Text part should be empty when citation is present');
    }

    const sourcePart = createSourcePart(citation, messageId);

    return sourcePart;
  }

  const textPart = createTextPart(text);

  return textPart;
}

export function processFilePart(part: FilePart): UIFilePart {
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

  return filePart;
}
