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

import { Tag } from '@carbon/react';
import type { TagBaseProps } from '@carbon/react/lib/components/Tag/Tag';

import { TagsList } from '#components/TagsList/TagsList.tsx';
import { isNotNull } from '#utils/helpers.ts';

import type { Agent } from '../api/types';
import { getAgentStatusMetadata } from '../utils';

interface Props {
  agent: Agent;
  className?: string;
  size?: TagBaseProps['size'];
}

export function AgentTags({ agent, className }: Props) {
  const { framework, license, tags } = agent.metadata;

  const { avg_run_time_seconds, avg_run_tokens } = getAgentStatusMetadata({
    agent,
    keys: ['avg_run_time_seconds', 'avg_run_tokens'],
  });

  const tagsElements = [
    framework,
    avg_run_time_seconds && `${avg_run_time_seconds}s/run (avg)`,
    avg_run_tokens && `${avg_run_tokens} tokens/run (avg)`,
    license,
    ...(tags ?? []),
  ]
    .filter(isNotNull)
    .map((value) => <AgentTag key={value} name={value} />);

  return <TagsList tags={tagsElements} className={className} />;
}

function AgentTag({ name }: { name: string }) {
  return <Tag type="cool-gray">{name}</Tag>;
}
