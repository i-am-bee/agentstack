/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { TaskIdParams } from '@a2a-js/sdk';
import { useMutation } from '@tanstack/react-query';

import { useAgentClient } from '#modules/runs/contexts/agent-client/index.ts';

import { cancelTask } from '..';

export function useCancelTask() {
  const { client } = useAgentClient();

  const mutation = useMutation({
    mutationFn: (params: TaskIdParams) => cancelTask(client, params),
    meta: {
      errorToast: false,
    },
  });

  return mutation;
}
