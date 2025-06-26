/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { MessagePart } from '#modules/runs/api/types.ts';

export type ComposeMessagePart = MessagePart & { agent_idx: number };
