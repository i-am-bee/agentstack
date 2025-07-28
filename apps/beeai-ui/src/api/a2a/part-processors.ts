/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FilePart, FileWithUri, TextPart } from '@a2a-js/sdk';
import { v4 as uuid } from 'uuid';

import type { UIFilePart, UIMessagePart, UISourcePart, UITextPart, UITrajectoryPart } from '#modules/messages/types.ts';
import { UIMessagePartKind } from '#modules/messages/types.ts';

import type { CitationMetadata } from './extensions/citation';
import { citationExtensionV1 } from './extensions/citation';
import { getExtensionData } from './extensions/getExtensionData';
import type { TrajectoryMetadata } from './extensions/trajectory';
import { trajectoryExtensionV1 } from './extensions/trajectory';

const extractCitations = getExtensionData(citationExtensionV1);
const extractTrajectory = getExtensionData(trajectoryExtensionV1);

function isFileWithUri(file: FilePart['file']): file is FileWithUri {
  return 'uri' in file;
}

function getFileUri(file: FilePart['file']): string {
  const isUriFile = isFileWithUri(file);

  if (isUriFile) {
    return file.uri;
  }

  const { mimeType = 'text/plain', bytes } = file;

  return `data:${mimeType};base64,${bytes}`;
}

function processFilePart(part: FilePart): Array<UIMessagePart> {
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

function processSourcePart(metadata: CitationMetadata, messageId: string): Array<UISourcePart> {
  const { url, start_index, end_index, title, description } = metadata;
  const id = uuid();

  if (!url) {
    return [];
  }

  const sourcePart: UISourcePart = {
    kind: UIMessagePartKind.Source,
    id,
    url,
    messageId,
    startIndex: start_index ?? undefined,
    endIndex: end_index ?? undefined,
    title: title ?? undefined,
    description: description ?? undefined,
  };

  return [sourcePart];
}

function processTrajectoryPart(metadata: TrajectoryMetadata): UITrajectoryPart {
  const { message, tool_name } = metadata;

  const part: UITrajectoryPart = {
    kind: UIMessagePartKind.Trajectory,
    id: uuid(),
    message: message ?? undefined,
    toolName: tool_name ?? undefined,
  };

  return part;
}

function processTextPart(messageId: string, part: TextPart): Array<UIMessagePart> {
  const citation = extractCitations(part.metadata);
  const trajectory = extractTrajectory(part.metadata);

  if (trajectory) {
    return [processTrajectoryPart(trajectory)];
  }

  if (citation) {
    if (part.text !== '') {
      throw new Error('Text part should be empty when citation is present');
    }

    return processSourcePart(citation, messageId);
  } else {
    const textPart: UITextPart = {
      kind: UIMessagePartKind.Text,
      id: uuid(),
      text: part.text,
    };

    return [textPart];
  }
}

export const PartProcessors = { processSourcePart, processTextPart, processFilePart, processTrajectoryPart };
