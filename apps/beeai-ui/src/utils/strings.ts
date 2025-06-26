/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export function isStringTerminalParameterSafe(value: string) {
  return /^[a-zA-Z0-9_-]*$/.test(value);
}
