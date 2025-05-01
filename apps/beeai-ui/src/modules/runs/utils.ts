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
import { Role } from './types';

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
  messagePart,
  sessionId,
}: {
  agent: AgentName;
  messagePart: MessagePart;
  sessionId?: SessionId;
}): CreateRunStreamRequest {
  return {
    agent_name: agent,
    input: [{ parts: [messagePart] }],
    mode: RunMode.Stream,
    session_id: sessionId,
  };
}

export function createMessagePart({
  content,
  content_encoding = 'plain',
  content_type = 'text/plain',
}: Partial<Exclude<MessagePart, 'role'>>): MessagePart {
  return {
    content,
    content_encoding,
    content_type,
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
