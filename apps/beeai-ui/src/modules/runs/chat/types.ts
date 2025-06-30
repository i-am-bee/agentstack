/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { TrajectoryMetadata } from '../api/types';
import type { SourceReference } from '../sources/api/types';
import type { Role } from '../types';

interface Message {
  key: string;
  role: Role;
  content: string;
  error?: unknown;
  files?: MessageFile[];
}
export interface UserMessage extends Message {
  role: Role.User;
}
export interface AssistantMessage extends Message {
  role: Role.Assistant;
  rawContent: string;
  contentTransforms: MessageContentTransform[];
  status: MessageStatus;
  sources?: SourceReference[];
  trajectories?: TrajectoryMetadata[];
}

export interface MessageFile {
  key: string;
  filename: string;
  href: string;
}

export interface MessageContentTransform {
  key: string;
  kind: MessageContentTransformType;
  startIndex: number;
  apply: ({ content, offset }: { content: string; offset: number }) => string;
}

export interface CitationTransform extends MessageContentTransform {
  kind: MessageContentTransformType.Citation;
  sources: SourceReference[];
}

export type ChatMessage = UserMessage | AssistantMessage;

export enum MessageStatus {
  InProgress = 'in-progress',
  Completed = 'completed',
  Aborted = 'aborted',
  Failed = 'failed',
}

export enum MessageContentTransformType {
  Citation = 'citation',
  Image = 'image',
}
