/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
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
