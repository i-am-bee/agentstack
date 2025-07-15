/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback, useRef, useState } from 'react';
import { v4 as uuidv4 } from 'uuid';

import { Agent } from '#modules/agents/api/types.ts';

import { useCancelRun } from '../api/mutations/useCancelRun';
import { useCreateRunStream } from '../api/mutations/useCreateRunStream';
import type {
  GenericEvent,
  MessageCompletedEvent,
  RunCancelledEvent,
  RunCompletedEvent,
  RunCreatedEvent,
  RunFailedEvent,
  RunId,
} from '../api/types';
import type { RunAgentParams } from '../types';

interface Props {
  agent: Agent;
  onBeforeRun?: () => void;
  onRunCreated?: (event: RunCreatedEvent) => void;
  onRunFailed?: (event: RunFailedEvent) => void;
  onRunCancelled?: (event: RunCancelledEvent) => void;
  onRunCompleted?: (event: RunCompletedEvent) => void;
  onMessagePart?: (content: string) => void;
  onMessageCompleted?: (event: MessageCompletedEvent) => void;
  onGeneric?: (event: GenericEvent) => void;
  onDone?: () => void;
  onStop?: () => void;
}

export function useRunAgent({
  agent,
  onBeforeRun,
  onMessagePart,
  // onRunCreated,
  // onRunFailed,
  // onRunCancelled,
  // onRunCompleted,
  // onMessageCompleted,
  // onGeneric,
  onDone,
  onStop,
}: Props) {
  const abortControllerRef = useRef<AbortController | null>(null);

  const [input, setInput] = useState<string>();
  const [isPending, setIsPending] = useState(false);
  const [runId, setRunId] = useState<RunId>();
  // TODO:
  // const [sessionId, setSessionId] = useState<SessionId>();

  const { mutateAsync: createRunStream } = useCreateRunStream(agent);
  const { mutate: cancelRun } = useCancelRun();

  const handleDone = useCallback(() => {
    setIsPending(false);

    onDone?.();
  }, [onDone]);

  const runAgent = useCallback(
    async ({ messageParts }: RunAgentParams) => {
      try {
        onBeforeRun?.();

        const content = messageParts.reduce((acc, part) => (part.kind === 'text' ? `${acc}\n${part.text}` : acc), '');

        setIsPending(true);
        setInput(content);

        const abortController = new AbortController();
        abortControllerRef.current = abortController;

        const stream = await createRunStream({
          message: {
            messageId: uuidv4(),
            role: 'user',
            parts: messageParts,
            kind: 'message',
          },
        });

        for await (const event of stream) {
          if (event.kind === 'status-update') {
            const message = event.status.message;

            if (!message) {
              continue;
            }

            onMessagePart?.(message.parts.map((part) => (part.kind === 'text' ? part.text : '')).join(''));
          }

          // case 'run.created':
          //   onRunCreated?.(event);
          //   setRunId(event.run.run_id);
          //   setSessionId(event.run.session_id ?? undefined);
          //   break;
          // case 'run.failed':
          //   handleDone();
          //   onRunFailed?.(event);
          //   break;
          // case 'run.cancelled':
          //   handleDone();
          //   onRunCancelled?.(event);
          //   break;
          // case 'run.completed':
          //   handleDone();
          //   onRunCompleted?.(event);
          //   break;
          // case 'message.part':
          //   onMessagePart?.(event);
          //   break;
          // case 'message.completed':
          //   onMessageCompleted?.(event);
          //   break;
          // case 'generic':
          //   onGeneric?.(event);
          //   break;
        }
      } catch (error) {
        handleDone();

        throw error;
      }
    },
    [onBeforeRun, createRunStream, handleDone, onMessagePart],
  );

  const stopAgent = useCallback(() => {
    if (!isPending) {
      return;
    }

    setIsPending(false);

    if (runId) {
      cancelRun(runId);
    }

    abortControllerRef.current?.abort();
    abortControllerRef.current = null;

    onStop?.();
  }, [isPending, runId, cancelRun, onStop]);

  const reset = useCallback(() => {
    stopAgent();
    setInput(undefined);
    setRunId(undefined);
    // setSessionId(undefined);
  }, [stopAgent]);

  return {
    input,
    isPending,
    runAgent,
    stopAgent,
    reset,
  };
}
