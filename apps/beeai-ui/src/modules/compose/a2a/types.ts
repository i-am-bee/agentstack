/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export interface UISequentialWorkflowPart {
  kind: UIComposePartKind.SequentialWorkflow;
  agentIdx: number;
  message: string;
}

export enum UIComposePartKind {
  SequentialWorkflow = 'sequential-workflow',
}

export type UIComposePart = UISequentialWorkflowPart;
