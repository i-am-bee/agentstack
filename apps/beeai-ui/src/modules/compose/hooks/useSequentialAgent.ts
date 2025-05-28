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

import { useAgent } from '#modules/agents/api/queries/useAgent.ts';
import { useAgentStatus } from '#modules/agents/hooks/useAgentStatus.ts';

import { SEQUENTIAL_WORKFLOW_AGENT_NAME } from '../sequential/constants';

export function useSequentialAgent() {
  const { data: agent } = useAgent({ name: SEQUENTIAL_WORKFLOW_AGENT_NAME });
  const { isReady } = useAgentStatus({ providerId: agent?.metadata.provider_id });

  return isReady ? agent : undefined;
}
