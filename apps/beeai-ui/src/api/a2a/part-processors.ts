/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FilePart, FileWithUri, TextPart } from '@a2a-js/sdk';
import { v4 as uuid } from 'uuid';

import type { UIFilePart, UISourcePart, UITextPart, UITrajectoryPart } from '#modules/messages/types.ts';
import { UIMessagePartKind } from '#modules/messages/types.ts';

import type { CitationMetadata } from './extensions/citation';
import { citationExtension } from './extensions/citation';
import { getExtensionData } from './extensions/getExtensionData';
import type { TrajectoryMetadata } from './extensions/trajectory';
import { trajectoryExtension } from './extensions/trajectory';

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

const extractCitation = getExtensionData(citationExtension);
const extractTrajectory = getExtensionData(trajectoryExtension);

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

function createSourcePart(metadata: CitationMetadata, messageId: string): UISourcePart | null {
  const { url, start_index, end_index, title, description } = metadata;

  if (!url) {
    return null;
  }

  const sourcePart: UISourcePart = {
    kind: UIMessagePartKind.Source,
    id: uuid(),
    url,
    messageId,
    startIndex: start_index ?? undefined,
    endIndex: end_index ?? undefined,
    title: title ?? undefined,
    description: description ?? undefined,
  };

  return sourcePart;
}

function createTrajectoryPart(metadata: TrajectoryMetadata): UITrajectoryPart {
  const { message, tool_name } = metadata;

  const trajectoryPart: UITrajectoryPart = {
    kind: UIMessagePartKind.Trajectory,
    id: uuid(),
    message: message ?? undefined,
    toolName: tool_name ?? undefined,
  };

  return trajectoryPart;
}

function createTextPart(text: string): UITextPart {
  const textPart: UITextPart = {
    kind: UIMessagePartKind.Text,
    id: uuid(),
    text,
  };

  return textPart;
}
