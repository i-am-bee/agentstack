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

import humanizeDuration from 'humanize-duration';
import JSON5 from 'json5';

import type { AgentName } from '#modules/agents/api/types.ts';
import { isNotNull } from '#utils/helpers.ts';

import {
  type Artifact,
  type CreateRunStreamRequest,
  type Message,
  type MessagePart,
  RunMode,
  type SessionId,
} from './api/types';
import { Role, type RunLog } from './types';

humanizeDuration.languages.shortEn = {
  h: () => 'h',
  m: () => 'min',
  s: () => 's',
};

export function runDuration(ms: number) {
  const duration = humanizeDuration(ms, {
    units: ['h', 'm', 's'],
    round: true,
    delimiter: ' ',
    spacer: '',
    language: 'shortEn',
  });

  return duration;
}

export function createRunStreamRequest({
  agent,
  messageParts,
  sessionId,
}: {
  agent: AgentName;
  messageParts: MessagePart[];
  sessionId?: SessionId;
}): CreateRunStreamRequest {
  return {
    agent_name: agent,
    input: [{ parts: messageParts }],
    mode: RunMode.Stream,
    session_id: sessionId,
  };
}

export function createMessagePart({
  content,
  content_encoding = 'plain',
  content_type = 'text/plain',
  content_url,
}: Partial<Exclude<MessagePart, 'role'>>): MessagePart {
  return {
    content,
    content_encoding,
    content_type,
    content_url,
    role: Role.User,
  };
}

export function isArtifact(part: MessagePart): part is Artifact {
  return typeof part.name === 'string';
}

export function extractOutput(messages: Message[]) {
  const output = messages
    .flatMap(({ parts }) => parts)
    .map(({ content }) => content)
    .filter(isNotNull)
    .join('');

  return output;
}

export function formatLog(log: RunLog) {
  const { message } = log;

  if (message && typeof parseJsonLikeString(message) === 'string') {
    return message;
  }

  return JSON.stringify(log);
}

const parseJsonLikeString = (string: string): unknown | string => {
  try {
    const json = JSON5.parse(string);

    return json;
  } catch {
    return string;
  }
};
