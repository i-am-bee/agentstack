/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useState } from 'react';

import { useToast } from '#contexts/Toast/index.ts';
import { TaskType, useTasks } from '#hooks/useTasks.ts';
import { useAgent } from '#modules/agents/api/queries/useAgent.ts';
import { useProviderStatus } from '#modules/agents/hooks/useProviderStatus.ts';

import { providerKeys } from '../api/keys';

interface Props {
  id?: string;
  isEnabled?: boolean;
}

export function useMonitorProviderStatus({ id, isEnabled }: Props) {
  const [isDone, setIsDone] = useState(false);
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  const { addTask, removeTask } = useTasks();

  const { refetch: refetchStatus, ...agentStatusReturn } = useProviderStatus({ providerId: id });
  const { data: agent } = useAgent({ providerId: id });

  const { isStarting, isNotInstalled } = agentStatusReturn;

  const shouldMonitorStatus = isEnabled && !isDone && (isStarting || isNotInstalled);

  const checkProvider = useCallback(async () => {
    const { isReady, isError } = await refetchStatus();

    if (agent) {
      if (isReady) {
        addToast({
          title: `${agent.name} has installed successfully.`,
          kind: 'info',
          timeout: 5_000,
        });
      } else if (isError) {
        addToast({
          title: `${agent.name} failed to install.`,
          timeout: 5_000,
        });
      }
    }

    if (isReady || isError) {
      queryClient.invalidateQueries({ queryKey: providerKeys.lists() });

      if (id) {
        removeTask({ id, type: TaskType.ProviderStatusCheck });
      }

      setIsDone(true);
    }
  }, [refetchStatus, agent, addToast, queryClient, id, removeTask]);

  useEffect(() => {
    if (id && shouldMonitorStatus) {
      addTask({
        id: id,
        type: TaskType.ProviderStatusCheck,
        task: checkProvider,
        delay: CHECK_PROVIDER_STATUS_INTERVAL,
      });

      return () => {
        removeTask({ id: id, type: TaskType.ProviderStatusCheck });
      };
    }
  }, [addTask, checkProvider, id, removeTask, shouldMonitorStatus]);

  return agentStatusReturn;
}

const CHECK_PROVIDER_STATUS_INTERVAL = 2000;
