/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FilePart, Message, TaskStatusUpdateEvent, TextPart } from '@a2a-js/sdk';
import { A2AClient } from '@a2a-js/sdk/client';
import { Subject } from 'rxjs';
import { match } from 'ts-pattern';
import { v4 as uuid } from 'uuid';

import type { FileEntity } from '#modules/files/types.ts';
import { getFileContentUrl, getFileUri } from '#modules/files/utils.ts';
import { Role } from '#modules/messages/api/types.ts';
import type { UIFilePart, UIMessagePart, UITextPart } from '#modules/messages/types.ts';
import { UIMessagePartKind } from '#modules/messages/types.ts';
import { processSourcePart } from '#modules/sources/utils.ts';
import { processTrajectoryPart } from '#modules/trajectories/utils.ts';

import { citationExtensionV1 } from './extensions/citation';
import { getExtensionData } from './extensions/getExtensionData';
import { trajectoryExtensionV1 } from './extensions/trajectory';

const extractCitations = getExtensionData(citationExtensionV1);
const extractTrajectory = getExtensionData(trajectoryExtensionV1);

export interface ChatRun {
  done: Promise<void>;
  subscribe: (fn: (parts: UIMessagePart[]) => void) => () => void;
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

function processTextPart(messageId: string, part: TextPart): Array<UIMessagePart> {
  const citation = extractCitations(part.metadata);
  const trajectory = extractTrajectory(part.metadata);

  if (trajectory) {
    return [processTrajectoryPart(trajectory)];
  }

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

  if (!message) {
    return [];
  }

  return message.parts.flatMap((part) => {
    const transformedParts = match(part)
      .with({ kind: 'text' }, (part) => processTextPart(message.messageId, part))
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
