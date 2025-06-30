/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useNavigate, useParams } from 'react-router';

import { Container } from '#components/layouts/Container.tsx';
import { MainContent } from '#components/layouts/MainContent.tsx';
import { AgentDetailView } from '#modules/agents/detail/AgentDetailView.tsx';
import type { AgentPageParams } from '#modules/agents/types.ts';
import { routes } from '#utils/router.ts';

export function Agent() {
  const { agentName } = useParams<AgentPageParams>();
  const navigate = useNavigate();

  if (!agentName) {
    navigate(routes.notFound(), { replace: true });
    return null;
  }

  return (
    <MainContent>
      <Container>
        <AgentDetailView name={agentName} />
      </Container>
    </MainContent>
  );
}
