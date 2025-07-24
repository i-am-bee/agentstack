/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { getErrorMessage } from '#api/utils.ts';
import { ErrorMessage } from '#components/ErrorMessage/ErrorMessage.tsx';
import type { UIAgentMessage } from '#modules/messages/types.ts';

import { checkMessageStatus } from '../utils';

interface Props {
  message: UIAgentMessage;
}

export function MessageError({ message }: Props) {
  const { isError, isFailed, error } = checkMessageStatus(message);

  if (!isError) {
    return;
  }

  return (
    <ErrorMessage
      title={isFailed ? 'Failed to generate an agent message.' : 'Message generation has been cancelled.'}
      subtitle={getErrorMessage(error)}
    />
  );
}
