/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Artifact, FilePart, Message, Part, TextPart } from 'agentstack-sdk';
import { match } from 'ts-pattern';
import { v4 as uuid } from 'uuid';

import type { UIFilePart, UIMessagePart, UISourcePart, UITextPart } from '#modules/messages/types.ts';
import { UIMessagePartKind } from '#modules/messages/types.ts';
import { isNotNull } from '#utils/helpers.ts';

import {
  createSourcePart,
  createTextPart,
  createTrajectoryPart,
  extractCitation,
  extractTrajectory,
  getFileUrl,
} from './utils';

export function processMessageMetadata(message: Message): UIMessagePart[] {
  const trajectory = extractTrajectory(message.metadata);
  const citations = extractCitation(message.metadata)?.citations;

  const parts: UIMessagePart[] = [];

  if (trajectory) {
    parts.push(createTrajectoryPart(trajectory));
  }
  if (citations) {
    const sourceParts = citations.map((citation) => createSourcePart(citation, message.taskId)).filter(isNotNull);

    parts.push(...sourceParts);
  }

  return parts;
}

export function processArtifactMetadata(artifact: Artifact, taskId: string): UISourcePart[] {
  const citations = extractCitation(artifact.metadata)?.citations;

  if (!citations) {
    return [];
  }

  return citations.map((citation) => createSourcePart(citation, taskId)).filter(isNotNull);
}

export function processTextPart({ text }: TextPart): UITextPart {
  return createTextPart(text);
}

function processFilePart(part: FilePart): UIFilePart {
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

  return filePart;
}

export function processParts(parts: Part[]) {
  const processedParts = parts
    .map((part) => {
      const processedParts = match(part)
        .with({ kind: 'text' }, processTextPart)
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
