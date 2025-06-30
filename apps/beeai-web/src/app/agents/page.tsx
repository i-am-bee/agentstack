/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Container, ViewStack } from '@i-am-bee/beeai-ui';

import { fetchAgentsList } from '@/api/fetchAgentsList';
import { MainContent } from '@/layouts/MainContent';

import { AgentsFilteredView } from './AgentsFilteredView';

export default async function AgentsPage() {
  const agents = await fetchAgentsList();

  return (
    <MainContent>
      <Container>
        <ViewStack>
          <AgentsFilteredView agents={agents} />
        </ViewStack>
      </Container>
    </MainContent>
  );
}
