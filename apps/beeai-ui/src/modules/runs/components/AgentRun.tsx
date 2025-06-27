/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type Agent, UiType } from '#modules/agents/api/types.ts';
import { getAgentUiMetadata } from '#modules/agents/utils.ts';

import { useAgent } from '../../agents/api/queries/useAgent';
import { ChatView } from '../chat/ChatView';
import { HandsOffView } from '../hands-off/HandsOffView';
import { UiFailedView } from './UiFailedView';
import { UiLoadingView } from './UiLoadingView';
import { UiNotAvailableView } from './UiNotAvailableView';

interface Props {
  name: string;
}

export function AgentRun({ name }: Props) {
  const { data: agent, error, isPending, isRefetching, refetch } = useAgent({ name });

  return !isPending ? (
    agent ? (
      renderUi({ agent })
    ) : (
      <UiFailedView message={error?.message} isRefetching={isRefetching} onRetry={refetch} />
    )
  ) : (
    <UiLoadingView />
  );
}

const renderUi = ({ agent }: { agent: Agent }) => {
  const { ui_type } = getAgentUiMetadata(agent);

  switch (ui_type) {
    case UiType.Chat:
      return <ChatView agent={agent} />;
    case UiType.HandsOff:
      return <HandsOffView agent={agent} />;
    default:
      return <UiNotAvailableView agent={agent} />;
  }
};
