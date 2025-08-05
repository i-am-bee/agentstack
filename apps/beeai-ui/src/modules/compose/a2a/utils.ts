/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { getExtensionData } from '#api/a2a/extensions/utils.ts';
import type { A2AClientStatusUpdateHandlerParams } from '#api/a2a/types.ts';
import type { UIDataPart } from '#modules/messages/types.ts';
import { UIMessagePartKind } from '#modules/messages/types.ts';

import type { ComposeStep } from '../contexts/compose-context';
import { sequentialWorkflowExtension } from './extensions/sequential-workflow';
import { UIComposePartKind } from './types';

export const extractSequentialWorkflowData = getExtensionData(sequentialWorkflowExtension);

export function createSequentailInputDataPart(steps: ComposeStep[]): UIDataPart {
  return {
    kind: UIMessagePartKind.Data,
    data: {
      input: '',
      steps: steps.map((step) => ({
        provider_id: step.agent.provider.id,
        instruction: step.instruction,
      })),
    },
  };
}

export function handleTaskStatusUpdate({ event, nativeHandler }: A2AClientStatusUpdateHandlerParams) {
  const message = event.status.message;
  const metadata = message?.metadata;

  const sequentialMetadata = extractSequentialWorkflowData(metadata);

  if (sequentialMetadata) {
    const { agent_idx, message } = sequentialMetadata;

    if (agent_idx !== undefined && message) {
      return [{ kind: UIComposePartKind.SequentialWorkflow, agentIdx: agent_idx, message }];
    }
  }

  return nativeHandler(event);
}
