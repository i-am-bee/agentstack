/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { type Agent, SupportedUIType } from '#modules/agents/api/types.ts';

import { ChatView } from '../chat/ChatView';
import { HandsOffView } from '../hands-off/HandsOffView';
import { UiNotAvailableView } from './UiNotAvailableView';

interface Props {
  agent: Agent;
}

export function RunView({ agent }: Props) {
  switch (agent.ui?.ui_type) {
    case SupportedUIType.Chat:
      return <ChatView agent={agent} key={agent.name} />;
    case SupportedUIType.HandsOff:
      return <HandsOffView agent={agent} key={agent.name} />;
    default:
      return <UiNotAvailableView agent={agent} />;
  }
}
