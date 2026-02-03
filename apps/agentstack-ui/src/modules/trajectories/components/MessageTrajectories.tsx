/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Spinner } from '#components/Spinner/Spinner.tsx';
import type { UIAgentMessage } from '#modules/messages/types.ts';
import { getMessageTrajectories } from '#modules/messages/utils.ts';

import classes from './MessageTrajectories.module.scss';
import { TrajectoryView } from './TrajectoryView';

interface Props {
  message: UIAgentMessage;
  isPending?: boolean;
}

export function MessageTrajectories({ message, isPending }: Props) {
  const trajectories = getMessageTrajectories(message);
  const hasTrajectories = trajectories.length > 0;

  if (!hasTrajectories) {
    if (isPending) {
      return (
        <div className={classes.spinner}>
          <Spinner center />
        </div>
      );
    }

    return null;
  }

  return <TrajectoryView trajectories={trajectories} isPending={isPending} />;
}
