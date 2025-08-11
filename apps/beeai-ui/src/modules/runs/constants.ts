/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { SupportedUIType } from '#modules/agents/api/types.ts';

export const SupportedUis: string[] = [SupportedUIType.Chat, SupportedUIType.HandsOff];

export const PROMPT_EXAMPLES_DIALOG_OFFSET = {
  mainAxis: 27, // Space between the input and the examples
};

export const RUN_SETTINGS_DIALOG_OFFSET = {
  mainAxis: 56,
  crossAxis: -12,
};
