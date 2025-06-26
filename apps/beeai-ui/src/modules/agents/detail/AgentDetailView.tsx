/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ErrorMessage } from '#components/ErrorMessage/ErrorMessage.tsx';

import { useAgent } from '../api/queries/useAgent';
import { AgentDetail } from '../components/AgentDetail';
import { AgentLaunchButton } from './AgentLaunchButton';

interface Props {
  name: string;
}

export function AgentDetailView({ name }: Props) {
  const { data: agent, isPending, error, refetch, isRefetching } = useAgent({ name });
  if (isPending) {
    return <AgentDetail.Skeleton />;
  }
  if (!agent) {
    return (
      <ErrorMessage
        title="Failed to load the agent."
        onRetry={refetch}
        isRefetching={isRefetching}
        subtitle={error?.message}
      />
    );
  }
  return <AgentDetail agent={agent} buttons={<AgentLaunchButton agent={agent} />} />;
}
