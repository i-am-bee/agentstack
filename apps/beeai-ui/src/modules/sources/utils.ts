/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { v4 as uuid } from 'uuid';

import type { UIMessage, UISourcePart, UITransformPart } from '#modules/messages/types.ts';
import { UIMessagePartKind, UITransformType } from '#modules/messages/types.ts';
import { getMessageSources } from '#modules/messages/utils.ts';
import { isNotNull } from '#utils/helpers.ts';
import { toMarkdownCitation } from '#utils/markdown.ts';

import type { MessageSourcesMap } from './types';
import { CitationMetadata } from '#modules/runs/hooks/extensions/citation.ts';

export function processSourcePart(metadata: CitationMetadata, messageId: string): (UISourcePart | UITransformPart)[] {
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

  const transformPart: UITransformPart = {
    kind: UIMessagePartKind.Transform,
    id: uuid(),
    type: UITransformType.Source,
    startIndex: start_index ?? Infinity,
    sources: [id],
    apply: function (content, offset) {
      const adjustedStartIndex = isNotNull(start_index) ? start_index + offset : content.length;
      const adjustedEndIndex = isNotNull(end_index) ? end_index + offset : content.length;
      const before = content.slice(0, adjustedStartIndex);
      const text = content.slice(adjustedStartIndex, adjustedEndIndex);
      const after = content.slice(adjustedEndIndex);

      return `${before}${toMarkdownCitation({ text, sources: this.sources })}${after}`;
    },
  };

  return [sourcePart, transformPart];
}

export function getMessageSourcesMap(messages: UIMessage[]) {
  const sources = messages.reduce<MessageSourcesMap>(
    (data, message) => ({
      ...data,
      [message.id]: getMessageSources(message),
    }),
    {},
  );

  return sources;
}
