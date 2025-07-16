/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { MessageSendParams } from '@a2a-js/sdk';
import { A2AClient } from '@a2a-js/sdk/client';
import { useMutation } from '@tanstack/react-query';
import { useMemo } from 'react';

import { Agent } from '#modules/agents/api/types.ts';

import { sendMessageStream } from '..';

export function useSendMessageStream(agent: Agent) {
  const client = useMemo(() => new A2AClient(`/api/v1/a2a/${agent.provider.id}`), [agent.provider.id]);

  const mutation = useMutation({
    mutationFn: (params: MessageSendParams) => sendMessageStream(client, params),
    meta: {
      errorToast: false,
    },
  });

  return mutation;
}
