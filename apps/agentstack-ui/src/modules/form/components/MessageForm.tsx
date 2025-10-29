/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMessages } from '#modules/messages/contexts/Messages/index.ts';
import type { UIAgentMessage } from '#modules/messages/types.ts';
import { getMessageForm } from '#modules/messages/utils.ts';
import { useAgentRun } from '#modules/runs/contexts/agent-run/index.ts';
import { blurActiveElement } from '#utils/dom-utils.ts';

import type { RunFormValues } from '../types';
import { FormRenderer } from './FormRenderer';

interface Props {
  message: UIAgentMessage;
}

export function MessageForm({ message }: Props) {
  const formPart = getMessageForm(message);
  const { submitRuntimeForm } = useAgentRun();
  const { isLastMessage } = useMessages();

  if (!formPart) {
    return null;
  }

  return (
    <FormRenderer
      definition={formPart}
      showHeading={false}
      isDisabled={!isLastMessage(message)}
      onSubmit={(values: RunFormValues) => {
        const form = {
          request: formPart,
          response: { id: formPart.id, values },
        };

        if (!message.taskId) {
          throw new Error('Illegal State');
        }

        submitRuntimeForm(form, message.taskId);

        blurActiveElement();
      }}
    />
  );
}
