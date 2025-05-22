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

import clsx from 'clsx';

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
  const userGreeting = agent.metadata.ui?.user_greeting;

  const isPendingOrOutput = Boolean(isPending || output);
  const isFinal = Boolean(output && !isPending);

  return (
    <HandsOffView>
      <div className={clsx(classes.root, { [classes.isPendingOrOutput]: isPendingOrOutput })}>
        <div className={classes.holder}>
          <div className={classes.header}>
            <AgentHeader agent={agent} onNewSessionClick={isPendingOrOutput ? onClear : undefined} />

            <h2 className={classes.heading}>{isFinal ? 'Task input:' : userGreeting || 'What is your task?'}</h2>
          </div>

          <div className={classes.body}>
            <HandsOffInput />

            {isFinal && (
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
