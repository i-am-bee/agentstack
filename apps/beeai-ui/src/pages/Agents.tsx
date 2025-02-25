/**
 * Copyright 2025 IBM Corp.
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

import { Container } from '#components/layouts/Container.tsx';
import { ViewStack } from '#components/ViewStack/ViewStack.tsx';
import { AgentsFilters } from '#modules/agents/components/AgentsFilters.tsx';
import { AgentsList } from '#modules/agents/components/AgentsList.tsx';

import { AgentsProvider } from '#modules/agents/contexts/AgentsProvider.tsx';

export function Agents() {
  return (
    <Container>
      <ViewStack>
        <AgentsProvider>
          <AgentsFilters />

          <AgentsList />
        </AgentsProvider>
      </ViewStack>
    </Container>
  );
}
