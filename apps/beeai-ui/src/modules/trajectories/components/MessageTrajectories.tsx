/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UIAgentMessage } from '#modules/messages/types.ts';
import { getMessageTrajectories } from '#modules/messages/utils.ts';

import { TrajectoryView } from './TrajectoryView';

interface Props {
  message: UIAgentMessage;
  toggleable?: boolean;
  autoScroll?: boolean;
}

export function MessageTrajectories({ message, toggleable = true, autoScroll }: Props) {
  const trajectories = getMessageTrajectories(message);
  const hasTrajectories = trajectories.length > 0;

  return hasTrajectories ? (
    <TrajectoryView trajectories={trajectories} toggleable={toggleable} autoScroll={autoScroll} />
  ) : null;
}
