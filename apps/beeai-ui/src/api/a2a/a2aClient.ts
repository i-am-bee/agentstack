/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FilePart, Message, TaskStatusUpdateEvent } from '@a2a-js/sdk';
import { A2AClient } from '@a2a-js/sdk/client';
import { Subject } from 'rxjs';
import { match } from 'ts-pattern';
import { v4 as uuid } from 'uuid';

import type { FileEntity } from '#modules/files/types.ts';
import { getFileContentUrl } from '#modules/files/utils.ts';
import type { UIMessagePart } from '#modules/messages/types.ts';

import { PartProcessors } from './part-processors';

export interface ChatRun {
  done: Promise<void>;
  subscribe: (fn: (parts: UIMessagePart[]) => void) => () => void;
  cancel: () => Promise<void>;
}

function convertFileEntityToFilePart(file: FileEntity): FilePart {
  if (!file.uploadFile) {
    throw new Error('File upload file is not present');
  }

  return {
    kind: 'file',
    file: {
      uri: getFileContentUrl({ id: file.uploadFile.id, addBase: true }),
      name: file.uploadFile.filename,
      mimeType: file.originalFile.type,
    },
  };
}

function handleStatusUpdate(event: TaskStatusUpdateEvent): UIMessagePart[] {
  const message = event.status.message;

  if (!message) {
    return [];
  }

  return message.parts.flatMap((part) => {
    const transformedParts = match(part)
      .with({ kind: 'text' }, (part) => PartProcessors.processTextPart(message.messageId, part))
      .with({ kind: 'file' }, PartProcessors.processFilePart)
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
    role: 'user',
  };
}

export const buildA2AClient = (agentUrl: string) => {
  const client = new A2AClient(agentUrl);

  const chat = (text: string, files: FileEntity[], contextId: string) => {
    const taskId = uuid();
    const messageSubject = new Subject<UIMessagePart[]>();

    const iterateOverStream = async () => {
      const res = await client.sendMessageStream({
        message: buildUserMessage(text, files, contextId, taskId),
      });

      for await (const event of res) {
        match(event).with({ kind: 'status-update' }, (event) => {
          const messageParts = handleStatusUpdate(event);
          messageSubject.next(messageParts);
        });
      }

      messageSubject.complete();
    };

    const run: ChatRun = {
      done: iterateOverStream(),
      subscribe: (fn) => {
        const subscription = messageSubject.subscribe(fn);

        return () => {
          subscription.unsubscribe();
        };
      },
      cancel: async () => {
        messageSubject.complete();
        await client.cancelTask({ id: taskId });
      },
    };

    return run;
  };

  return { chat };
};
