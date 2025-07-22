/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UITrajectoryPart } from '#modules/messages/types.ts';

import classes from './TrajectoryItemContent.module.scss';

interface Props {
  trajectory: UITrajectoryPart;
}

export function TrajectoryItemContent({ trajectory }: Props) {
  const { message } = trajectory;

  return (
    <div className={classes.root}>
      <div className={classes.group}>
        <p className={classes.label}>Thought</p>

        <p className={classes.content}>{message}</p>
      </div>
    </div>
  );
}
