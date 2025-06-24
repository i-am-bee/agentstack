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

import { useCallback, useRef, useState } from 'react';

import { handleStream } from '#api/utils.ts';

import { useCancelRun } from '../api/mutations/useCancelRun';
import { useCreateRunStream } from '../api/mutations/useCreateRunStream';
import type {
  ArtifactEvent,
  GenericEvent,
  MessageCompletedEvent,
  MessagePartEvent,
  RunCancelledEvent,
  RunCompletedEvent,
  RunCreatedEvent,
  RunEvent,
  RunFailedEvent,
  RunId,
  SessionId,
} from '../api/types';
import { EventType } from '../api/types';
import type { RunAgentParams } from '../types';
import { createRunStreamRequest } from '../utils';

interface Props {
  onBeforeRun?: () => void;
  onRunCreated?: (event: RunCreatedEvent) => void;
  onRunFailed?: (event: RunFailedEvent) => void;
  onRunCancelled?: (event: RunCancelledEvent) => void;
  onRunCompleted?: (event: RunCompletedEvent) => void;
  onMessagePart?: (event: ArtifactEvent | MessagePartEvent) => void;
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
          body: createRunStreamRequest({
            agent: agent.name,
            messageParts,
            sessionId,
          }),
          signal: abortController.signal,
        });

        handleStream<RunEvent>({
          stream,
          onEvent: (event) => {
            switch (event.type) {
              case EventType.RunCreated:
                onRunCreated?.(event);
                setRunId(event.run.run_id);
                setSessionId(event.run.session_id);

                break;
              case EventType.RunFailed:
                handleDone();
                onRunFailed?.(event);

                break;
              case EventType.RunCancelled:
                handleDone();
                onRunCancelled?.(event);

                break;
              case EventType.RunCompleted:
                handleDone();
                onRunCompleted?.(event);

                break;
              case EventType.MessagePart:
                onMessagePart?.(event);

                break;
              case EventType.MessageCompleted:
                onMessageCompleted?.(event);

                break;
              case EventType.Generic:
                onGeneric?.(event);

                break;
            }
          },
        });
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
      cancelRun({ run_id: runId });
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
