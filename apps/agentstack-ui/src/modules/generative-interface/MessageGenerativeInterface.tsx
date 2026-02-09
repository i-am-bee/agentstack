/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { useCallback, useState } from 'react';

import { useMessages } from '#modules/messages/contexts/Messages/index.ts';
import type { UIAgentMessage } from '#modules/messages/types.ts';
import { getMessageGenerativeInterface } from '#modules/messages/utils.ts';
import { useAgentRun } from '#modules/runs/contexts/agent-run/index.ts';

import { GenerativeInterfaceRenderer } from './GenerativeInterfaceRenderer';

interface Props {
  message: UIAgentMessage;
}

export function MessageGenerativeInterface({ message }: Props) {
  const part = getMessageGenerativeInterface(message);
  const { submitGenerativeInterface } = useAgentRun();
  const { isLastMessage } = useMessages();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleButtonClick = useCallback(
    async (elementKey: string) => {
      if (!part) {
        return;
      }

      setIsSubmitting(true);
      try {
        await submitGenerativeInterface(
          { component_id: elementKey, event_type: 'button_click' },
          part.taskId,
        );
      } finally {
        setIsSubmitting(false);
      }
    },
    [part, submitGenerativeInterface],
  );

  const isCurrentMessageLast = isLastMessage(message);

  if (!part || !isCurrentMessageLast) {
    return null;
  }

  return <GenerativeInterfaceRenderer spec={part.spec} onButtonClick={handleButtonClick} loading={isSubmitting} />;
}
