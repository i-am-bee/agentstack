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

import { InlineLoading } from '@carbon/react';

import type { Agent } from '../api/types';
import { useProviderStatus } from '../hooks/useProviderStatus';
import classes from './AgentStatusIndicator.module.scss';

interface Props {
  agent: Agent;
}

export function AgentStatusIndicator({ agent }: Props) {
  const { provider_id } = agent.metadata;
  const { isStarting } = useProviderStatus({ providerId: provider_id });

  if (isStarting) {
    return (
      <div className={classes.root}>
        <InlineLoading />
      </div>
    );
  }
  return null;
}
