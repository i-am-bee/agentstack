/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useNavigate, useParams } from 'react-router';

import type { AgentPageParams } from '#modules/agents/types.ts';
import { AgentRun } from '#modules/runs/components/AgentRun.tsx';
import { routes } from '#utils/router.ts';

export function AgentRunPage() {
  const { agentName } = useParams<AgentPageParams>();
  const navigate = useNavigate();

  if (!agentName) {
    navigate(routes.notFound(), { replace: true });
    return null;
  }

  return <AgentRun name={agentName} />;
}
