/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
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
