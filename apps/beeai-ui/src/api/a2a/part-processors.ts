/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FilePart, Message, Part, TextPart } from '@a2a-js/sdk';
import { match } from 'ts-pattern';
import { v4 as uuid } from 'uuid';

import type { UIFilePart, UIMessagePart } from '#modules/messages/types.ts';
import { UIMessagePartKind } from '#modules/messages/types.ts';
import { isNotNull } from '#utils/helpers.ts';

import {
  createFormPart,
  createSourcePart,
  createTextPart,
  createTrajectoryPart,
  extractCitation,
  extractForm,
  extractTrajectory,
  getFileUrl,
} from './utils';

export function processMessageMetadata(message: Message): UIMessagePart[] {
  const trajectory = extractTrajectory(message.metadata);
  const citations = extractCitation(message.metadata)?.citations;
  const form = extractForm(message.metadata);

  const parts: UIMessagePart[] = [];

  if (trajectory) {
    parts.push(createTrajectoryPart(trajectory));
  }
  if (citations) {
    const sourceParts = citations.map((citation) => createSourcePart(citation, message.taskId)).filter(isNotNull);

    parts.push(...sourceParts);
  }
  if (form) {
    parts.push(createFormPart(form));
  }

  return parts;
}

export function processTextPart({ text }: TextPart): UIMessagePart[] {
  return [createTextPart(text)];
}

export function processFilePart(part: FilePart): UIMessagePart[] {
  const { file } = part;
  const { name, mimeType } = file;
  const id = uuid();
  const url = getFileUrl(file);

  const filePart: UIFilePart = {
    kind: UIMessagePartKind.File,
    url,
    id,
    filename: name || id,
    type: mimeType,
  };

  return [filePart];
}

export function processParts(parts: Part[]): UIMessagePart[] {
  const processedParts = parts
    .flatMap((part) => {
      const processedParts = match(part)
        .with({ kind: 'text' }, (part) => processTextPart(part))
        .with({ kind: 'file' }, processFilePart)
        .otherwise((otherPart) => {
          console.warn(`Unsupported part - ${otherPart.kind}`);

          return null;
        });

      return processedParts;
    })
    .filter(isNotNull);

  return processedParts;
}
