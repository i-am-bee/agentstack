/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { TaskStatusUpdateEvent } from '@a2a-js/sdk';
import { A2AClient } from '@a2a-js/sdk/client';
import { Subject } from 'rxjs';
import { match } from 'ts-pattern';
import { v4 as uuid } from 'uuid';

import type { FileEntity } from '#modules/files/types.ts';
import type { UIMessagePart } from '#modules/messages/types.ts';
import { getBaseUrl } from '#utils/api/getBaseUrl.ts';
import { isNotNull } from '#utils/helpers.ts';

import { processFilePart, processTextPart } from './part-processors';
import { createUserMessage } from './utils';

export interface ChatRun {
  done: Promise<void>;
  subscribe: (fn: (parts: UIMessagePart[]) => void) => () => void;
  cancel: () => Promise<void>;
}

function handleStatusUpdate(event: TaskStatusUpdateEvent): UIMessagePart[] {
  const { message } = event.status;

  if (!message) {
    return [];
  }

  const parts = message.parts
    .map((part) => {
      const processedPart = match(part)
        .with({ kind: 'text' }, (part) => processTextPart(part, message.messageId))
        .with({ kind: 'file' }, processFilePart)
        .otherwise((otherPart) => {
          throw new Error(`Unsupported part - ${otherPart.kind}`);
        });

      return processedPart;
    })
    .filter(isNotNull);

  return parts;
}

export const buildA2AClient = (agentId: string) => {
  const agentUrl = `${getBaseUrl()}/api/v1/a2a/${agentId}`;
  const client = new A2AClient(agentUrl);

  // HACK: the URL in the agent card is not using the nextjs proxy - we need to replace it
  // eslint-disable-next-line
  (client as unknown as any).agentCardPromise.then(() => {
    // eslint-disable-next-line
    (client as unknown as any).serviceEndpointUrl = agentUrl;
  });

  const chat = (text: string, files: FileEntity[], contextId: string) => {
    const taskId = uuid();
    const messageSubject = new Subject<UIMessagePart[]>();

    const iterateOverStream = async () => {
      const stream = client.sendMessageStream({
        message: createUserMessage(text, files, contextId, taskId),
      });

      for await (const event of stream) {
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
