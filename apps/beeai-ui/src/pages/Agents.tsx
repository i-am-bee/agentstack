/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Container } from '#components/layouts/Container.tsx';
import { MainContent } from '#components/layouts/MainContent.tsx';
import { ViewStack } from '#components/ViewStack/ViewStack.tsx';
import { AgentsView } from '#modules/agents/list/AgentsView.tsx';
import { AgentsFiltersProvider } from '#modules/agents/providers/AgentsFiltersProvider.tsx';

export function Agents() {
  return (
    <MainContent>
      <Container>
        <ViewStack>
          <AgentsFiltersProvider>
            <AgentsView />
          </AgentsFiltersProvider>
        </ViewStack>
      </Container>
    </MainContent>
  );
}
