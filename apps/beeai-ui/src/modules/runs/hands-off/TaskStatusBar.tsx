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

import { ElapsedTime } from '../components/ElapsedTime';
import { StatusBar } from '../components/StatusBar';
import { useAgent } from '../contexts/agent';
import { useHandsOff } from '../contexts/hands-off';

interface Props {
  onStopClick?: () => void;
}

export function TaskStatusBar({ onStopClick }: Props) {
  const { stats, isPending } = useHandsOff();
  const {
    status: { isNotInstalled, isStarting },
  } = useAgent();

  return stats?.startTime ? (
    <StatusBar isPending={isPending} onStopClick={onStopClick}>
      {isNotInstalled || isStarting ? (
        'Starting the agent, please bee patient...'
      ) : (
        <>
          Task {isPending ? 'running for' : 'completed in'} <ElapsedTime stats={stats} />
        </>
      )}
    </StatusBar>
  ) : null;
}
