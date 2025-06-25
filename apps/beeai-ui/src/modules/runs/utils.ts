/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
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
import type { UploadFileResponse } from './files/api/types';
import type { FileEntity } from './files/types';
import { getFileContentUrl } from './files/utils';
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
    input: [
      {
        parts: messageParts,
        role: `agent/${agent}`,
      },
    ],
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

export function createFileMessageParts(files: UploadFileResponse[]) {
  const messageParts = files.map(({ id }) =>
    createMessagePart({ content_url: getFileContentUrl({ id, addBase: true }) }),
  );

  return messageParts;
}

export function isArtifactPart(part: MessagePart): part is Artifact {
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

export function extractValidUploadFiles(files: FileEntity[]) {
  const uploadFiles = files.map(({ uploadFile }) => uploadFile).filter(isNotNull);

  return uploadFiles;
}

export function mapToMessageFiles(uploadFiles: UploadFileResponse[]) {
  return uploadFiles.map(({ id, filename }) => ({ key: id, filename, href: getFileContentUrl({ id }) }));
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
