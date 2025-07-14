/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { Tag } from '@carbon/react';
import type { TagBaseProps } from '@carbon/react/lib/components/Tag/Tag';

import { TagsList } from '#components/TagsList/TagsList.tsx';
import { isNotNull } from '#utils/helpers.ts';

import type { Agent } from '../api/types';

interface Props {
  agent: Agent;
  className?: string;
  size?: TagBaseProps['size'];
}

export function AgentTags({ agent, className }: Props) {
  const { framework, license, tags, avg_run_time_seconds, avg_run_tokens } = agent.ui;

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
