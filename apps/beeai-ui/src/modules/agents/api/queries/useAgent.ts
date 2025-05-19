/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
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

import { useQuery } from '@tanstack/react-query';

import { listAgents } from '..';
import { agentKeys } from '../keys';
import type { Agent, ReadAgentPath } from '../types';

export function useAgent({ name }: ReadAgentPath) {
  return useQuery({
    queryKey: agentKeys.list(),
    // TODO: We could use the `/api/v1/acp/agents/{name}` endpoint to fetch the exact agent, but currently we are listing
    // all the agents at once, so we can reuse the data here untill the agents have sorting and pagination.
    queryFn: listAgents,
    select: (data) => {
      const agent = data?.agents.find((item) => name === item.name);

      return agent as Agent;
    },
  });
}
