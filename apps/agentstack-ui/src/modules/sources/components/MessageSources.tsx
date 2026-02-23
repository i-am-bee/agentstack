/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UIAgentMessage } from '#modules/messages/types.ts';
import { getMessageSources } from '#modules/messages/utils.ts';

import { SourcesGroup } from './SourcesGroup';

interface Props {
  message: UIAgentMessage;
}

export function MessageSources({ message }: Props) {
  const sources = getMessageSources(message);

  return <SourcesGroup sources={sources} taskId={message.taskId} />;
}
