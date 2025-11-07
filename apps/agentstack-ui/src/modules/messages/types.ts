/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Task } from '@a2a-js/sdk';
import type { FormRender, SecretDemands } from 'agentstack-sdk';

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
  | UISecretPart;

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
  title?: string;
  content?: string;
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
);

export type UIDataPart = {
  kind: UIMessagePartKind.Data;
  data: Record<string, unknown>;
};

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
}

export interface UIMessageForm {
  request: FormRender;
  response: RunFormValues;
}
