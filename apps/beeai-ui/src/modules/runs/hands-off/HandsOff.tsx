/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';

import { AgentGreeting } from '#modules/agents/components/AgentGreeting.tsx';

import { AgentHeader } from '../components/AgentHeader';
import { AgentRunLogs } from '../components/AgentRunLogs';
import { ElapsedTime } from '../components/ElapsedTime';
import { useHandsOff } from '../contexts/hands-off';
import classes from './HandsOff.module.scss';
import { HandsOffInput } from './HandsOffInput';
import { HandsOffView } from './HandsOffView';
import { TaskStatusBar } from './TaskStatusBar';

export function HandsOff() {
  const { agent, logs, output, isPending, stats, onClear } = useHandsOff();

  const isPendingOrOutput = Boolean(isPending || output);
  const isCompleted = Boolean(output && !isPending);

  return (
    <HandsOffView>
      <div className={clsx(classes.root, { [classes.isPendingOrOutput]: isPendingOrOutput })}>
        <div className={classes.holder}>
          <div className={classes.header}>
            <AgentHeader agent={agent} onNewSessionClick={isPendingOrOutput ? onClear : undefined} />

            {isCompleted ? (
              <h2 className={classes.heading}>Task input:</h2>
            ) : (
              <AgentGreeting agent={agent} className={classes.heading} defaultGreeting="What is your task?" />
            )}
          </div>

          <div className={classes.body}>
            <HandsOffInput />

            {isCompleted && (
              <span className={classes.elapsed}>
                Task completed in <ElapsedTime stats={stats} />
              </span>
            )}

            {logs && <AgentRunLogs logs={logs} toggleable={Boolean(output)} />}

            {isPending && <TaskStatusBar />}
          </div>
        </div>
      </div>
    </HandsOffView>
  );
}
