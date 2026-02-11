/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { useMessages } from '#modules/messages/contexts/Messages/index.ts';
import type { UIAgentMessage } from '#modules/messages/types.ts';
import { UIMessagePartKind } from '#modules/messages/types.ts';
import { useAgentRun } from '#modules/runs/contexts/agent-run/index.ts';
import { blurActiveElement } from '#utils/dom-utils.ts';

import type { RunFormValues } from '../types';
import { FormRenderer } from './FormRenderer';
import classes from './MessageTextInput.module.scss';

interface Props {
  message: UIAgentMessage;
}

export function MessageTextInput({ message }: Props) {
  const textInputPart = message.parts.find(
    (part): part is Extract<typeof part, { kind: UIMessagePartKind.TextInput }> =>
      part.kind === UIMessagePartKind.TextInput,
  );
  const { submitTextInput } = useAgentRun();
  const { isLastMessage } = useMessages();

  const formDefinition = useMemo(() => {
    if (!textInputPart) return null;

    return {
      title: textInputPart.text,
      fields: [
        {
          id: 'text',
          type: 'text' as const,
          label: textInputPart.text,
          required: true,
          auto_resize: true,
        },
      ],
    };
  }, [textInputPart]);

  if (!formDefinition || !textInputPart || !isLastMessage(message)) {
    return null;
  }

  return (
    <FormRenderer
      className={classes.form}
      definition={formDefinition}
      showHeading={false}
      onSubmit={(values: RunFormValues) => {
        const fieldValue = values.text;
        const textValue = fieldValue?.type === 'text' ? fieldValue.value : null;

        submitTextInput(textValue ?? '', textInputPart.taskId);
        blurActiveElement();
      }}
    />
  );
}
