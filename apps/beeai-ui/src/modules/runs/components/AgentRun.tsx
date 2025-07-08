/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { type Agent, UiType } from '#modules/agents/api/types.ts';
import { getAgentUiMetadata } from '#modules/agents/utils.ts';

import { ChatView } from '../chat/ChatView';
import { HandsOffView } from '../hands-off/HandsOffView';
import { UiNotAvailableView } from './UiNotAvailableView';

interface Props {
  agent: Agent;
}

export function AgentRun({ agent }: Props) {
  const { ui_type } = getAgentUiMetadata(agent);

  switch (ui_type) {
    case UiType.Chat:
      return <ChatView agent={agent} key={agent.name} />;
    case UiType.HandsOff:
      return <HandsOffView agent={agent} key={agent.name} />;
    default:
      return <UiNotAvailableView agent={agent} />;
  }
}
