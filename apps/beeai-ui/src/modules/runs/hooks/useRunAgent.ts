/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback, useRef, useState } from 'react';

import { useCancelRun } from '../api/mutations/useCancelRun';
import { useCreateRunStream } from '../api/mutations/useCreateRunStream';
import type {
  GenericEvent,
  Message,
  MessageCompletedEvent,
  MessagePartEvent,
  RunCancelledEvent,
  RunCompletedEvent,
  RunCreatedEvent,
  RunFailedEvent,
  RunId,
  SessionId,
} from '../api/types';
import type { RunAgentParams } from '../types';

interface Props {
  onBeforeRun?: () => void;
  onRunCreated?: (event: RunCreatedEvent) => void;
  onRunFailed?: (event: RunFailedEvent) => void;
  onRunCancelled?: (event: RunCancelledEvent) => void;
  onRunCompleted?: (event: RunCompletedEvent) => void;
  onMessagePart?: (event: MessagePartEvent) => void;
  onMessageCompleted?: (event: MessageCompletedEvent) => void;
  onGeneric?: (event: GenericEvent) => void;
  onDone?: () => void;
  onStop?: () => void;
}

export function useRunAgent({
  onBeforeRun,
  onRunCreated,
  onRunFailed,
  onRunCancelled,
  onRunCompleted,
  onMessagePart,
  onMessageCompleted,
  onGeneric,
  onDone,
  onStop,
}: Props = {}) {
  const abortControllerRef = useRef<AbortController | null>(null);

  const [input, setInput] = useState<string>();
  const [isPending, setIsPending] = useState(false);
  const [runId, setRunId] = useState<RunId>();
  const [sessionId, setSessionId] = useState<SessionId>();

  const { mutateAsync: createRunStream } = useCreateRunStream();
  const { mutate: cancelRun } = useCancelRun();

  const handleDone = useCallback(() => {
    setIsPending(false);

    onDone?.();
  }, [onDone]);

  const runAgent = useCallback(
    async ({ agent, messageParts }: RunAgentParams) => {
      try {
        onBeforeRun?.();

        const content = messageParts.reduce((acc, { content }) => (content ? `${acc}\n${content}` : acc), '');

        setIsPending(true);
        setInput(content);

        const abortController = new AbortController();
        abortControllerRef.current = abortController;

        const stream = await createRunStream({
          body: {
            agentName: agent.name,
            input: [
              {
                parts: messageParts,
                role: 'user',
              } as Message,
            ],
            sessionId: sessionId ?? undefined,
          },
          signal: abortController.signal,
        });

        for await (const event of stream) {
          switch (event.type) {
            case 'run.created':
              onRunCreated?.(event);
              setRunId(event.run.run_id);
              setSessionId(event.run.session_id ?? undefined);
              break;
            case 'run.failed':
              handleDone();
              onRunFailed?.(event);
              break;
            case 'run.cancelled':
              handleDone();
              onRunCancelled?.(event);
              break;
            case 'run.completed':
              handleDone();
              onRunCompleted?.(event);
              break;
            case 'message.part':
              onMessagePart?.(event);
              break;
            case 'message.completed':
              onMessageCompleted?.(event);
              break;
            case 'generic':
              onGeneric?.(event);
              break;
          }
        }
      } catch (error) {
        handleDone();

        throw error;
      }
    },
    [
      onBeforeRun,
      createRunStream,
      sessionId,
      onRunCreated,
      handleDone,
      onRunFailed,
      onRunCancelled,
      onRunCompleted,
      onMessagePart,
      onMessageCompleted,
      onGeneric,
    ],
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
    setSessionId(undefined);
  }, [stopAgent]);

  return {
    input,
    isPending,
    runAgent,
    stopAgent,
    reset,
  };
}
