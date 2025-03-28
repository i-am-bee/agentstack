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

import { useNavigate, useParams } from 'react-router';

import { Container } from '#components/layouts/Container.tsx';
import { MainContent } from '#components/layouts/MainContent.tsx';
import { AgentDetailView } from '#modules/agents/detail/AgentDetailView.tsx';
import { routes } from '#utils/router.ts';

type Params = {
  agentName: string;
};

export function Agent() {
  const { agentName } = useParams<Params>();
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
