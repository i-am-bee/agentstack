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

import { ElapsedTime } from '../components/ElapsedTime';
import { useHandsOff } from '../contexts/hands-off';
import classes from './TaskStatusBar.module.scss';

interface Props {
  onStopClick?: () => void;
}

export function TaskStatusBar({ onStopClick }: Props) {
  const { stats, isPending } = useHandsOff();

  return stats?.startTime ? (
    <div className={classes.root}>
      <div className={classes.label}>
        {isPending && <Spinner center />}
        <span>
          Task {isPending ? 'running for' : 'completed in'} <ElapsedTime stats={stats} />
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
