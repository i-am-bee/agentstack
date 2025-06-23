/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { v4 as uuid } from 'uuid';

import type { CitationMetadata } from '../api/types';
import type { AssistantMessage, ChatMessage } from '../chat/types';
import { Role } from '../types';
import type { ResolvedSource, SourceReference, SourcesData } from './api/types';

export function resolveSource({ source, data }: { source: SourceReference; data: ResolvedSource | undefined }) {
  return data ?? { ...source, metadata: { title: source.url } };
}

export function prepareMessageSources({
  message,
  metadata,
}: {
  message: AssistantMessage;
  metadata: CitationMetadata;
}) {
  const { url, start_index, end_index } = metadata;
  const { sources: prevSources = [] } = message;

  const key = uuid();

  const sources: SourceReference[] = [
    ...prevSources,
    {
      key,
      url,
      startIndex: start_index,
      endIndex: end_index,
      messageKey: message.key,
    },
  ]
    .sort((a, b) => a.startIndex - b.startIndex)
    .map((source, idx) => ({
      ...source,
      number: idx + 1,
    }));

  const newSource = sources.find((source) => source.key === key)!;

  return { sources, newSource };
}

export function extractSources(messages: ChatMessage[]) {
  const sources = messages.reduce<SourcesData>((data, message) => {
    if (message.role === Role.Assistant && message.sources) {
      return {
        ...data,
        [message.key]: message.sources,
      };
    }

    return data;
  }, {});

  return sources;
}
