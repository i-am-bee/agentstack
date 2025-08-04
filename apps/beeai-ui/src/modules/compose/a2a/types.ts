export interface UISequentialWorkflowPart {
  kind: UIComposePartKind.SequentialWorkflow;
  agentIdx: number;
  message: string;
}

export enum UIComposePartKind {
  SequentialWorkflow = 'sequential-workflow',
}

export type UIComposePart = UISequentialWorkflowPart;
