/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { TaskIdParams } from '@a2a-js/sdk';
import { A2AClient } from '@a2a-js/sdk/client';
import { useMutation } from '@tanstack/react-query';
import { useMemo } from 'react';

import { Agent } from '#modules/agents/api/types.ts';

import { cancelTask } from '..';

export function useCancelTask(agent: Agent) {
  const client = useMemo(() => new A2AClient(`/api/v1/a2a/${agent.provider.id}`), [agent.provider.id]);

  const mutation = useMutation({
    mutationFn: (params: TaskIdParams) => cancelTask(client, params),
    meta: {
      errorToast: false,
    },
  });

  return mutation;
}
