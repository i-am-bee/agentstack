/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Agent } from '#modules/agents/api/types.ts';
import type { UIAgentMessage } from '#modules/messages/types.ts';
import { getMessageRawContent } from '#modules/messages/utils.ts';
import type { ContextId } from '#modules/tasks/api/types.ts';

import { type FeedbackForm, FeedbackVote } from '../types';
import type { SendFeedbackRequest } from './types';

export function createSendFeedbackPayload({
  agent,
  message,
  values,
  contextId,
}: {
  agent: Agent;
  message: UIAgentMessage;
  values: FeedbackForm;
  contextId: ContextId;
}): SendFeedbackRequest {
  const { vote, categories, comment } = values;

  return {
    rating: vote === FeedbackVote.Up ? 1 : -1,
    comment_tags: categories?.map(({ id }) => id),
    comment,
    message: getMessageRawContent(message),
    provider_id: agent.provider.id,
    context_id: contextId,
    task_id: message.id,
  };
}
