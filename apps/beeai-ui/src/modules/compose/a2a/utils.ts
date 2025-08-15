/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { TaskStatusUpdateEvent } from '@a2a-js/sdk';

import { extractUiExtensionData } from '#api/a2a/extensions/utils.ts';
import type { UIDataPart } from '#modules/messages/types.ts';
import { UIMessagePartKind } from '#modules/messages/types.ts';

import type { ComposeStep } from '../contexts/compose-context';
import { sequentialWorkflowExtension } from './extensions/sequential-workflow';
import { UIComposePartKind } from './types';

export const extractSequentialWorkflowData = extractUiExtensionData(sequentialWorkflowExtension);

export function createSequentialInputDataPart(steps: ComposeStep[]): UIDataPart {
  return {
    kind: UIMessagePartKind.Data,
    data: {
      steps: steps.map((step) => ({
        provider_id: step.agent.provider.id,
        instruction: step.instruction,
      })),
    },
  };
}

export function handleTaskStatusUpdate(event: TaskStatusUpdateEvent) {
  const metadata = event.status.message?.metadata;

  const sequentialMetadata = extractSequentialWorkflowData(metadata);

  if (sequentialMetadata) {
    const { agent_idx, message } = sequentialMetadata;

    if (agent_idx !== undefined && message) {
      return [{ kind: UIComposePartKind.SequentialWorkflow, agentIdx: agent_idx, message }];
    }
  }

  return [];
}
