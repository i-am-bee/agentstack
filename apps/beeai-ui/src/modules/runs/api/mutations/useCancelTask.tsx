/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { TaskIdParams } from '@a2a-js/sdk';
import { useMutation } from '@tanstack/react-query';

import { useAgentClient } from '../../contexts/agent-client';
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
