/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Message, Part, Task, TaskArtifactUpdateEvent, TaskStatusUpdateEvent } from '@a2a-js/sdk';
import { useCallback, useState } from 'react';
import { v4 as uuid } from 'uuid';

import { useCancelTask } from '../api/mutations/useCancelTask';
import { useSendMessageStream } from '../api/mutations/useSendMessageStream';
import type { ContextId, TaskId } from '../api/types';
import { Role, type RunAgentParams } from '../types';
import { extractTextFromParts } from '../utils';

interface Props {
  onStart?: () => void;
  onStop?: () => void;
  onDone?: () => void;
  onPart?: (part: Part) => void;
  onCompleted?: (event: TaskStatusUpdateEvent) => void;
  onFailed?: (event: TaskStatusUpdateEvent, error: Error) => void;
}

export function useRunAgent({ onStart, onStop, onDone, onPart, onCompleted, onFailed }: Props) {
  const [input, setInput] = useState<string>();
  const [taskId, setTaskId] = useState<TaskId>();
  const [contextId, setContextId] = useState<ContextId>();
  const [isPending, setIsPending] = useState<boolean>(false);

  const { mutateAsync: sendMessageStream } = useSendMessageStream();
  const { mutate: cancelTask } = useCancelTask();

  const handleStart = useCallback(() => {
    setIsPending(true);

    onStart?.();
  }, [onStart]);

  const handleStop = useCallback(() => {
    setIsPending(false);
    setTaskId(undefined);

    onStop?.();
  }, [onStop]);

  const handleDone = useCallback(() => {
    setIsPending(false);
    setTaskId(undefined);

    onDone?.();
  }, [onDone]);

  const handlePart = useCallback(
    (part: Part) => {
      onPart?.(part);
    },
    [onPart],
  );

  const handleCompleted = useCallback(
    (event: TaskStatusUpdateEvent) => {
      handleDone();

      onCompleted?.(event);
    },
    [onCompleted, handleDone],
  );

  const handleFailed = useCallback(
    (event: TaskStatusUpdateEvent) => {
      handleDone();

      const parts = event.status.message?.parts;
      const errorMessage = (parts ? extractTextFromParts(parts) : '') || AGENT_ERROR_MESSAGE;

      onFailed?.(event, new Error(errorMessage));
    },
    [onFailed, handleDone],
  );

  const handleEvent = useCallback(
    (event: Task | Message | TaskStatusUpdateEvent | TaskArtifactUpdateEvent) => {
      if (contextId !== event.contextId) {
        setContextId(event.contextId);
      }
    },
    [contextId],
  );

  const handleTask = useCallback(
    (event: Task) => {
      if (taskId !== event.id) {
        setTaskId(event.id);
      }
    },
    [taskId],
  );

  const handleStatusUpdate = useCallback(
    (event: TaskStatusUpdateEvent) => {
      const {
        status: { message, state },
      } = event;

      message?.parts.forEach(handlePart);

      if (event.final) {
        handleCompleted(event);
      }

      switch (state) {
        case 'canceled':
          handleDone();

          break;
        case 'unknown':
          handleDone();

          break;
        case 'failed':
          handleFailed(event);

          break;
        case 'rejected':
          handleFailed(event);

          break;
      }
    },
    [handlePart, handleCompleted, handleDone, handleFailed],
  );

  const runAgent = useCallback(
    async ({ parts }: RunAgentParams) => {
      handleStart();

      setInput(extractTextFromParts(parts));

      const message: Message = {
        kind: 'message',
        messageId: uuid(),
        role: Role.User,
        parts,
        taskId,
        contextId,
      };

      try {
        const stream = await sendMessageStream({ message });

        for await (const event of stream) {
          handleEvent(event);

          switch (event.kind) {
            case 'task':
              handleTask(event);

              break;
            case 'status-update':
              handleStatusUpdate(event);

              break;
          }
        }
      } catch (error) {
        handleDone();

        throw error;
      }
    },
    [taskId, contextId, handleStart, sendMessageStream, handleEvent, handleTask, handleStatusUpdate, handleDone],
  );

  const stopAgent = useCallback(() => {
    if (!isPending) {
      return;
    }

    if (taskId) {
      cancelTask({ id: taskId });
    }

    handleStop();
  }, [isPending, taskId, cancelTask, handleStop]);

  const reset = useCallback(() => {
    stopAgent();

    setInput(undefined);
    setContextId(undefined);
  }, [stopAgent]);

  return {
    input,
    isPending,
    runAgent,
    stopAgent,
    reset,
  };
}

const AGENT_ERROR_MESSAGE = "An error occurred. The agent didn't provide any additional details.";
