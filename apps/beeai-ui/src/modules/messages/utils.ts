/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FilePart, Part, TextPart } from '@a2a-js/sdk';
import { v4 as uuid } from 'uuid';

import { getFileContentUrl } from '#modules/files/utils.ts';
import { isNotNull } from '#utils/helpers.ts';

import { Role } from './api/types';
import type {
  UIAgentMessage,
  UIMessage,
  UIMessagePart,
  UISourcePart,
  UITextPart,
  UITransformPart,
  UIUserMessage,
} from './types';
import { UIMessagePartKind, UIMessageStatus, UITransformType } from './types';

export function isUserMessage(message: UIMessage): message is UIUserMessage {
  return message.role === Role.User;
}

export function isAgentMessage(message: UIMessage): message is UIAgentMessage {
  return message.role === Role.Agent;
}

export function processMessageContent(message: UIMessage) {
  let offset = 0;

  const rawContent = message.parts.reduce(
    (content, part) => (part.kind === UIMessagePartKind.Text ? content.concat(part.text) : content),
    '',
  );
  const transformedContent = message.parts.reduce((content, part) => {
    if (part.kind === UIMessagePartKind.Transform) {
      const newContent = part.apply(content, offset);
      offset += newContent.length - content.length;

      return newContent;
    }

    return content;
  }, rawContent);

  return transformedContent;
}

export function getMessageFiles(message: UIMessage) {
  const files = message.parts.filter((part) => part.kind === UIMessagePartKind.File);

  return files;
}

export function getMessageSources(message: UIMessage) {
  const sources = message.parts.filter((part) => part.kind === UIMessagePartKind.Source);

  return sources;
}

export function getMessageTrajectories(message: UIMessage) {
  const trajectories = message.parts.filter((part) => part.kind === UIMessagePartKind.Trajectory);

  return trajectories;
}

export function checkMessageError(message: UIAgentMessage) {
  const { status } = message;
  const isError = status === UIMessageStatus.Failed || status === UIMessageStatus.Aborted;

  return isError;
}

export function convertUIMessageParts(uiParts: UIMessagePart[]): Part[] {
  const parts: Part[] = uiParts
    .map((part) => {
      switch (part.kind) {
        case UIMessagePartKind.Text:
          const { text } = part;

          return {
            kind: 'text',
            text,
          } as TextPart;
        case UIMessagePartKind.File:
          const { id, filename, type } = part;

          return {
            kind: 'file',
            file: {
              uri: getFileContentUrl({ id, addBase: true }),
              name: filename,
              mimeType: type,
            },
          } as FilePart;
      }
    })
    .filter(isNotNull);

  return parts;
}

export function processTextPart(part: TextPart): UITextPart {
  const uiPart: UITextPart = {
    kind: UIMessagePartKind.Text,
    id: uuid(),
    text: part.text,
  };

  return uiPart;
}

export function sortMessageParts(parts: UIMessagePart[]): UIMessagePart[] {
  const [sourceParts, otherParts, transformParts] = parts.reduce<[UISourcePart[], UIMessagePart[], UITransformPart[]]>(
    ([sources, others, transforms], part) => {
      switch (part.kind) {
        case UIMessagePartKind.Source:
          return [[...sources, part], others, transforms];

        case UIMessagePartKind.Transform:
          return [sources, others, [...transforms, part]];

        default:
          return [sources, [...others, part], transforms];
      }
    },
    [[], [], []],
  );

  // Sort sources by startIndex in ascending order and place items with undefined startIndex at the end
  const sortedSourceParts = sourceParts
    .sort((a, b) => (a.startIndex ?? Infinity) - (b.startIndex ?? Infinity))
    .map((source, idx) => ({
      ...source,
      number: idx + 1,
    }));

  // Sort transforms by startIndex in ascending order and group items with the same startIndex into one
  const sortedTransformParts = transformParts
    .reduce<UITransformPart[]>((parts, part) => {
      const { type, startIndex } = part;

      if (type === UITransformType.Source) {
        const existingPart = parts
          .filter((part) => part.type === UITransformType.Source)
          .find((part) => part.startIndex === startIndex);

        if (existingPart) {
          existingPart.sources.push(...part.sources);

          return parts;
        }
      }

      return [...parts, part];
    }, [])
    .sort((a, b) => a.startIndex - b.startIndex);

  // Transforms must be at the end
  return [...otherParts, ...sortedSourceParts, ...sortedTransformParts];
}
