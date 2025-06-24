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
import type { PropsWithChildren } from 'react';

import { Spinner } from '#components/Spinner/Spinner.tsx';

import classes from './StatusBar.module.scss';

interface Props {
  isPending?: boolean;
  onStopClick?: () => void;
}

export function StatusBar({ isPending, onStopClick, children }: PropsWithChildren<Props>) {
  return (
    <div className={classes.root}>
      <div className={classes.label}>
        {isPending && <Spinner center />}

        <span>{children}</span>
      </div>

      {onStopClick && (
        <Button kind="tertiary" size="sm" renderIcon={StopFilled} onClick={onStopClick}>
          Stop
        </Button>
      )}
    </div>
  );
}
