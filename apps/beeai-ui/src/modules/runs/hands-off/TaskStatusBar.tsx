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

import { StopFilled } from '@carbon/icons-react';
import { Button } from '@carbon/react';

import { Spinner } from '#components/Spinner/Spinner.tsx';
import { useAgentStatus } from '#modules/agents/hooks/useAgentStatus.ts';
import { useMonitorProvider } from '#modules/providers/hooks/useMonitorProviderStatus.ts';

import { ElapsedTime } from '../components/ElapsedTime';
import { useHandsOff } from '../contexts/hands-off';
import classes from './TaskStatusBar.module.scss';

interface Props {
  onStopClick?: () => void;
}

export function TaskStatusBar({ onStopClick }: Props) {
  const { agent, stats, isPending } = useHandsOff();

  useMonitorProvider({ id: agent.metadata.provider_id });

  const { status, isNotInstalled, isStarting } = useAgentStatus({ providerId: agent.metadata.provider_id });

  console.log({ status });

  return stats?.startTime ? (
    <div className={classes.root}>
      <div className={classes.label}>
        {isPending && <Spinner center />}
        <span>
          {isNotInstalled || isStarting ? (
            'Starting the agent, please bee patient...'
          ) : (
            <>
              Task {isPending ? 'running for' : 'completed in'} <ElapsedTime stats={stats} />
            </>
          )}
        </span>
      </div>

      {onStopClick && (
        <Button kind="tertiary" size="sm" renderIcon={StopFilled} onClick={onStopClick}>
          Stop
        </Button>
      )}
    </div>
  ) : null;
}
