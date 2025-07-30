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

export function transformSourcePart(sourcePart: UISourcePart): UITransformPart {
  const { id, startIndex, endIndex } = sourcePart;

  const transformPart: UITransformPart = {
    kind: UIMessagePartKind.Transform,
    id: uuid(),
    type: UITransformType.Source,
    startIndex: startIndex ?? Infinity,
    sources: [id],
    apply: function (content, offset) {
      const adjustedStartIndex = isNotNull(startIndex) ? startIndex + offset : content.length;
      const adjustedEndIndex = isNotNull(endIndex) ? endIndex + offset : content.length;
      const before = content.slice(0, adjustedStartIndex);
      const text = content.slice(adjustedStartIndex, adjustedEndIndex);
      const after = content.slice(adjustedEndIndex);

      return `${before}${toMarkdownCitation({ text, sources: this.sources })}${after}`;
    },
  };

  return transformPart;
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
