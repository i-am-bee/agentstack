/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { MessageSendParams } from '@a2a-js/sdk';
import { useMutation } from '@tanstack/react-query';

import { useAgentClient } from '../../contexts/agent-client';
import { sendMessageStream } from '..';

export function useSendMessageStream() {
  const { client } = useAgentClient();

  const mutation = useMutation({
    mutationFn: (params: MessageSendParams) => sendMessageStream(client, params),
    meta: {
      errorToast: false,
    },
  });

  return mutation;
}
