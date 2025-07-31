/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FilePart, FileWithUri, Message } from '@a2a-js/sdk';
import { v4 as uuid } from 'uuid';

import type { FileEntity } from '#modules/files/types.ts';
import { getFileContentUrl } from '#modules/files/utils.ts';
import type { UISourcePart, UITextPart, UITrajectoryPart } from '#modules/messages/types.ts';
import { UIMessagePartKind } from '#modules/messages/types.ts';
import type { ContextId, TaskId } from '#modules/tasks/api/types.ts';

import type { CitationMetadata } from './extensions/citation';
import { citationExtension } from './extensions/citation';
import type { TrajectoryMetadata } from './extensions/trajectory';
import { trajectoryExtension } from './extensions/trajectory';
import { getExtensionData } from './extensions/utils';

export const extractCitation = getExtensionData(citationExtension);

export const extractTrajectory = getExtensionData(trajectoryExtension);

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

export function createUserMessage({
  text,
  files,
  taskId,
  contextId,
}: {
  text: string;
  files: FileEntity[];
  contextId: ContextId;
  taskId?: TaskId;
}): Message {
  return {
    kind: 'message',
    messageId: uuid(),
    contextId,
    taskId,
    parts: [
      {
        kind: 'text',
        text,
      },
      ...files.map(convertFileToFilePart),
    ],
    role: 'user',
  };
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

export function createSourcePart(metadata: CitationMetadata, messageId: string): UISourcePart | null {
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

export function createTrajectoryPart(metadata: TrajectoryMetadata): UITrajectoryPart {
  const { message, tool_name } = metadata;

  const trajectoryPart: UITrajectoryPart = {
    kind: UIMessagePartKind.Trajectory,
    id: uuid(),
    message: message ?? undefined,
    toolName: tool_name ?? undefined,
  };

  return trajectoryPart;
}

export function createTextPart(text: string): UITextPart {
  const textPart: UITextPart = {
    kind: UIMessagePartKind.Text,
    id: uuid(),
    text,
  };

  return textPart;
}
