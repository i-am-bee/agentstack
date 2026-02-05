/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type {
  ApprovalRequest,
  ApprovalResponse,
  FormRender,
  SecretDemands,
  Task,
  TaskArtifactUpdateEvent,
} from 'agentstack-sdk';

import type { UICanvasEditRequestParams } from '#modules/canvas/types.ts';
import type { RunFormValues } from '#modules/form/types.ts';
import type { TaskId } from '#modules/tasks/api/types.ts';

import type { Role } from './api/types';

export interface UITask extends Omit<Task, 'history'> {
  messages: UIMessage[];
}

export interface UIMessageBase {
  id: string;
  role: Role;
  parts: UIMessagePart[];
  taskId?: TaskId;
  error?: Error;
}

export interface UIUserMessage extends UIMessageBase {
  role: Role.User;
  form?: UIMessageForm;
  auth?: string;
  canvasEditParams?: UICanvasEditRequestParams;
}

export interface UIAgentMessage extends UIMessageBase {
  role: Role.Agent;
  status: UIMessageStatus;
  artifactId?: string;
}

export type UIMessage = UIUserMessage | UIAgentMessage;

export type UIMessagePart =
  | UITextPart
  | UIFilePart
  | UIDataPart
  | UISourcePart
  | UITrajectoryPart
  | UIFormPart
  | UIAuthPart
  | UITransformPart
  | UISecretPart
  | UIArtifactPart
  | UIApprovalPart
  | UIApprovalResponsePart;

export type UITextPart = {
  kind: UIMessagePartKind.Text;
  id: string;
  text: string;
};

export type UIFilePart = {
  kind: UIMessagePartKind.File;
  id: string;
  url: string;
  filename: string;
  type?: string;
};

export type UISourcePart = {
  kind: UIMessagePartKind.Source;
  id: string;
  url: string;
  taskId: string;
  number: number | null;
  startIndex?: number;
  endIndex?: number;
  title?: string;
  description?: string;
  faviconUrl?: string;
};

export type UITrajectoryPart = {
  kind: UIMessagePartKind.Trajectory;
  id: string;
  groupId?: string;
  title?: string;
  content?: string;
  createdAt?: number;
};

export type UIFormPart = {
  kind: UIMessagePartKind.Form;
  render: FormRender;
};

export type UIAuthPart = {
  kind: UIMessagePartKind.OAuth;
  url: string;
  taskId: TaskId;
};

export type UISecretPart = {
  kind: UIMessagePartKind.SecretRequired;
  secret: SecretDemands;
  taskId: TaskId;
};

export type UIApprovalPart = {
  kind: UIMessagePartKind.ApprovalRequired;
  request: ApprovalRequest;
  taskId: TaskId;
};

export type UIApprovalResponsePart = {
  kind: UIMessagePartKind.ApprovalResponse;
  result: ApprovalResponse;
};

export type UITransformPart = {
  kind: UIMessagePartKind.Transform;
  id: string;
  startIndex: number;
  apply: (content: string, offset: number) => string;
} & (
  | {
      type: UITransformType.Image;
    }
  | {
      type: UITransformType.Source;
      sources: string[];
    }
  | {
      type: UITransformType.Artifact;
      artifactId: string;
    }
);

export type UIDataPart = {
  kind: UIMessagePartKind.Data;
  data: Record<string, unknown>;
};

export type UIArtifactPart = {
  kind: UIMessagePartKind.Artifact;
  parts: (UITextPart | UIFilePart)[];
} & Pick<TaskArtifactUpdateEvent['artifact'], 'artifactId' | 'name' | 'description'>;

export enum UIMessagePartKind {
  Text = 'text',
  File = 'file',
  Data = 'data',
  Source = 'source',
  Trajectory = 'trajectory',
  Form = 'form',
  OAuth = 'oauth',
  SecretRequired = 'secret-required',
  Transform = 'transform',
  Artifact = 'artifact',
  ApprovalRequired = 'approval-required',
  ApprovalResponse = 'approval-response',
}

export enum UIMessageStatus {
  InProgress = 'in-progress',
  Completed = 'completed',
  InputRequired = 'input-required',
  Aborted = 'aborted',
  Failed = 'failed',
}

export enum UITransformType {
  Source = 'source',
  Image = 'image',
  Artifact = 'artifact',
}

export interface UIMessageForm {
  request: FormRender;
  response: RunFormValues;
}
