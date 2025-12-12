/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export const connectorKeys = {
  all: () => ['connectors'] as const,
  list: () => [...connectorKeys.all(), 'list'] as const,
  presetsList: () => [...connectorKeys.all(), 'presets'] as const,
};
