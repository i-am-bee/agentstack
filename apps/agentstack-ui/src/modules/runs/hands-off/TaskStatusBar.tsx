/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import { RunElapsedTime } from '../components/RunElapsedTime';
import { RunStatusBar } from '../components/RunStatusBar';
import { useAgentRun } from '../contexts/agent-run';
import { useAgentStatus } from '../contexts/agent-status';

interface Props {
  onStopClick?: () => void;
}

export function TaskStatusBar({ onStopClick }: Props) {
  const { stats, isPending } = useAgentRun();
  const {
    status: { isNotInstalled, isStarting },
  } = useAgentStatus();

  return stats?.startTime ? (
    <RunStatusBar isPending={isPending} onStopClick={onStopClick}>
      {isNotInstalled || isStarting ? (
        'Starting the agent, please bee patient...'
      ) : (
        <>
          Task {isPending ? 'running for' : 'completed in'} <RunElapsedTime stats={stats} />
        </>
      )}
    </RunStatusBar>
  ) : null;
}
