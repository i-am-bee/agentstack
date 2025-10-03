/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import uniqBy from 'lodash/uniqBy';
import { v4 as uuid } from 'uuid';

import type { UIMessage, UISourcePart, UITransformPart } from '#modules/messages/types.ts';
import { UIMessagePartKind, UITransformType } from '#modules/messages/types.ts';
import { getMessageSources } from '#modules/messages/utils.ts';
import { isNotNull } from '#utils/helpers.ts';
import { toMarkdownCitation } from '#utils/markdown.ts';

import type { ActiveSource } from './contexts/types';
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

export function getMessagesSourcesMap(messages: UIMessage[]) {
  const sources = messages.reduce<MessageSourcesMap>((data, message) => {
    const { taskId } = message;

    if (!taskId) {
      return data;
    }

    return {
      ...data,
      [taskId]: getMessageSources(message),
    };
  }, {});

  return sources;
}

export function isSourceActive(source: UISourcePart, activeSource: ActiveSource | null) {
  const { taskId, number } = source;

  return activeSource?.taskId === taskId && isNotNull(number) && activeSource?.number === number;
}

export function getUniqueSources(sources: UISourcePart[]) {
  return uniqBy(sources, 'number');
}
