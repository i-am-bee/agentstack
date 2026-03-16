/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FilePart, Message, Part, TextPart } from 'agentstack-sdk';
import {
  type Citation,
  citationExtension,
  errorExtension,
  extractUiExtensionData,
  trajectoryExtension,
  type TrajectoryMetadata,
} from 'agentstack-sdk';
import truncate from 'lodash/truncate';
import { v4 as uuid } from 'uuid';

import { getFileContentUrl } from '#modules/files/utils.ts';
import type {
  UIMessagePart,
  UISourcePart,
  UITextPart,
  UITrajectoryPart,
  UIUserMessage,
} from '#modules/messages/types.ts';
import { UIMessagePartKind } from '#modules/messages/types.ts';
import type { ContextId, TaskId } from '#modules/tasks/api/types.ts';
import { isNotNull } from '#utils/helpers.ts';

import { PLATFORM_FILE_CONTENT_URL_BASE } from './constants';

export const extractCitation = extractUiExtensionData(citationExtension);
export const extractTrajectory = extractUiExtensionData(trajectoryExtension);
export const extractErrorExtension = extractUiExtensionData(errorExtension);

export function convertMessageParts(uiParts: UIMessagePart[]): Part[] {
  const parts: Part[] = uiParts
    .map((part) => {
      switch (part.kind) {
        case UIMessagePartKind.Text:
          const { text } = part;

          return {
            text,
          } as TextPart;
        case UIMessagePartKind.File:
          const { id, filename, type } = part;

          return {
            url: getFilePlatformUrl(id),
            filename,
            mediaType: type,
          } as FilePart;
        case UIMessagePartKind.Data:
          return part;
      }
    })
    .filter(isNotNull);

  return parts;
}

export function createUserMessage({
  message,
  contextId,
  taskId,
  metadata,
}: {
  message: UIUserMessage;
  contextId: ContextId;
  taskId?: TaskId;
  metadata?: Record<string, unknown>;
}): Message {
  return {
    role: 'ROLE_USER',
    messageId: message.id,
    contextId,
    taskId,
    parts: convertMessageParts(message.parts),
    metadata,
  };
}

export function isFilePartWithUrl(part: FilePart): boolean {
  return !!part.url;
}

export function getFileUrl(part: FilePart): string {
  if (part.url) {
    const url = part.url;
    if (url.startsWith(PLATFORM_FILE_CONTENT_URL_BASE)) {
      const fileId = url.replace(PLATFORM_FILE_CONTENT_URL_BASE, '');
      return getFileContentUrl(fileId);
    }
    return url;
  }

  const { mediaType = 'text/plain', raw = '' } = part;

  return `data:${mediaType};base64,${raw}`;
}

export function createSourcePart(citation: Citation, taskId: string | undefined | null): UISourcePart | null {
  const { url, start_index, end_index, title, description } = citation;

  if (!url || !taskId) {
    return null;
  }

  const sourcePart: UISourcePart = {
    kind: UIMessagePartKind.Source,
    id: uuid(),
    url,
    taskId,
    number: null,
    startIndex: start_index ?? undefined,
    endIndex: end_index ?? undefined,
    title: title ?? undefined,
    description: description ?? undefined,
  };

  return sourcePart;
}

export function createTrajectoryPart(metadata: TrajectoryMetadata): UITrajectoryPart {
  const { title, content, group_id } = metadata;

  const trajectoryPart: UITrajectoryPart = {
    kind: UIMessagePartKind.Trajectory,
    id: uuid(),
    groupId: group_id ?? undefined,
    title: title ?? undefined,
    content: truncate(content ?? undefined, { length: MAX_CONTENT_CHARS_LENGTH }),
    createdAt: Date.now(),
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

export function getFilePlatformUrl(id: string) {
  return `${PLATFORM_FILE_CONTENT_URL_BASE}${id}`;
}

export function getFileIdFromFilePlatformUrl(url: string) {
  const fileId = url.replace(PLATFORM_FILE_CONTENT_URL_BASE, '');

  return fileId;
}

const MAX_CONTENT_CHARS_LENGTH = 16000;
