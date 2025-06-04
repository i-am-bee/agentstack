/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useState } from 'react';

import { useToast } from '#contexts/Toast/index.ts';
import { TaskType, useTasks } from '#hooks/useTasks.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { useAgentStatus } from '#modules/agents/hooks/useAgentStatus.ts';

import { providerKeys } from '../api/keys';

interface Props {
  id?: string;
}

export function useMonitorProvider({ id }: Props) {
  const [isDone, setIsDone] = useState(false);
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  const { addTask, removeTask } = useTasks();

  const { refetch: refetchStatus, isStarting, isNotInstalled } = useAgentStatus({ providerId: id });
  const { data: agents } = useListAgents();

  const checkProvider = useCallback(async () => {
    const { isReady, isError } = await refetchStatus();

    if (isReady) {
      agents?.forEach(({ name }) => {
        addToast({
          title: `${name} has installed successfully.`,
          kind: 'info',
          timeout: 5_000,
        });
      });
    } else if (isError) {
      agents?.forEach(({ name }) => {
        addToast({
          title: `${name} failed to install.`,
          timeout: 5_000,
        });
      });
    }

    if (isReady || isError) {
      queryClient.invalidateQueries({ queryKey: providerKeys.lists() });

      if (id) {
        removeTask({ id, type: TaskType.ProviderStatusCheck });
      }

      setIsDone(true);
    }
  }, [id, agents, queryClient, refetchStatus, addToast, removeTask]);

  useEffect(() => {
    if (id && !isDone && (isStarting || isNotInstalled)) {
      addTask({
        id,
        type: TaskType.ProviderStatusCheck,
        task: checkProvider,
        delay: CHECK_PROVIDER_STATUS_INTERVAL,
      });

      return () => {
        removeTask({ id, type: TaskType.ProviderStatusCheck });
      };
    }
  }, [id, isDone, addTask, removeTask, checkProvider, isStarting, isNotInstalled]);
}

const CHECK_PROVIDER_STATUS_INTERVAL = 2000;
