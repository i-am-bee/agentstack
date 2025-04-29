/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import type { Role } from '../types';

interface Message {
  key: string;
  role: Role;
  content: string;
  error?: Error;
}
export interface UserMessage extends Message {
  role: Role.User;
}
export interface AssistantMessage extends Message {
  role: Role.Assistant;
  status: MessageStatus;
}

export type ChatMessage = UserMessage | AssistantMessage;

export type SendMessageParams = { input: string };

export enum MessageStatus {
  InProgress = 'in-progress',
  Completed = 'completed',
  Aborted = 'aborted',
  Failed = 'failed',
}

export enum RunStatus {
  Created = 'created',
  InProgress = 'in-progress',
  Awaiting = 'awaiting',
  Cancelling = 'cancelling',
  Cancelled = 'cancelled',
  Completed = 'completed',
  Failed = 'failed',
}
