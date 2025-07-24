/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Role } from '#modules/messages/api/types.ts';
import { UIFilePart, UIMessagePart, UIMessagePartKind, UITextPart } from '#modules/messages/types.ts';
import { FileEntity } from '#modules/files/types.ts';
import { getFileContentUrl, getFileUri } from '#modules/files/utils.ts';

import { FilePart, Message, TaskStatusUpdateEvent, TextPart } from '@a2a-js/sdk';
import { A2AClient } from '@a2a-js/sdk/client';

import { v4 as uuid } from 'uuid';
import { match } from 'ts-pattern';
import { processSourcePart } from '#modules/sources/utils.ts';
import { getExtensionData } from './extensions/getExtensionData';
import { citationExtensionV1 } from './extensions/citation';

const extractCitations = getExtensionData(citationExtensionV1);

export interface ChatRun {
  subscribe: (fn: (parts: UIMessagePart[]) => void) => void;
  cancel: () => Promise<void>;
}

// TODO: decouple with processFilePart in utils.ts
function processFilePart(part: FilePart): Array<UIMessagePart> {
  const { file } = part;
  const { name, mimeType } = file;
  const id = uuid();
  const url = getFileUri(file);

  const filePart: UIFilePart = {
    kind: UIMessagePartKind.File,
    url,
    id,
    filename: name || id,
    type: mimeType,
  };

  return [filePart];
}

function convertFileEntityToFilePart(file: FileEntity): FilePart {
  return {
    kind: 'file',
    file: {
      uri: getFileContentUrl({ id: file.id, addBase: true }),
    },
  };
}

function processTextPart(messageId: string, part: TextPart): Array<UIMessagePart> {
  const citation = extractCitations(part.metadata);
  if (citation) {
    if (part.text !== '') {
      throw new Error('Text part should be empty when citation is present');
    }

    return processSourcePart(citation, messageId);
  } else {
    const textPart: UITextPart = {
      kind: UIMessagePartKind.Text,
      id: uuid(),
      text: part.text,
    };

    return [textPart];
  }
}

function handleStatusUpdate(event: TaskStatusUpdateEvent): UIMessagePart[] {
  const message = event.status.message;

  // TODO: can we ignore this?
  if (!message) {
    return [];
  }

  return message.parts.flatMap((part) => {
    const transformedParts = match(part)
      .with({ kind: 'text' }, (part) => processTextPart('TODO', part))
      .with({ kind: 'file' }, processFilePart)
      .otherwise((otherPart) => {
        throw new Error(`Unsupported part - ${otherPart.kind}`);
      });

    return transformedParts;
  });
}

function buildUserMessage(message: string, files: FileEntity[], contextId: string, taskId: string): Message {
  return {
    kind: 'message',
    contextId,
    messageId: uuid(),
    taskId,
    parts: [{ kind: 'text', text: message }, ...files.map(convertFileEntityToFilePart)],
    role: Role.User,
  };
}

export const buildA2AClient = (agentUrl: string) => {
  const client = new A2AClient(agentUrl);

  const chat = async (text: string, files: FileEntity[], contextId: string) => {
    const taskId = uuid();

    const res = await client.sendMessageStream({
      message: buildUserMessage(text, files, contextId, taskId),
    });

    // TODO: move rxjs
    let subscribers: ((parts: UIMessagePart[]) => void)[] = [];

    const iterateOverStream = async () => {
      for await (const event of res) {
        match(event).with({ kind: 'status-update' }, (event) => {
          const messageParts = handleStatusUpdate(event);

          subscribers.forEach((subscriber) => {
            subscriber(messageParts);
          });
        });
      }
    };

    const done = iterateOverStream();

    const run: ChatRun = {
      subscribe: (fn: (text: UIMessagePart[]) => void) => {
        subscribers.push(fn);

        return done;
      },
      cancel: async () => {
        await client.cancelTask({ id: taskId });
      },
    };

    return run;
  };

  return { chat };
};
