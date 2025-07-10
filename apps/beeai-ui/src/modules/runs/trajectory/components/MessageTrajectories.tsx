/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentMessage } from '#modules/runs/chat/types.ts';

import { TrajectoryView } from './TrajectoryView';

interface Props {
  message: AgentMessage;
  toggleable?: boolean;
  autoScroll?: boolean;
}

export function MessageTrajectories({ message, toggleable = true, autoScroll }: Props) {
  const trajectories = message.trajectories ?? [];
  const hasTrajectories = trajectories.length > 0;

  return hasTrajectories ? (
    <TrajectoryView trajectories={trajectories} toggleable={toggleable} autoScroll={autoScroll} />
  ) : null;
}
