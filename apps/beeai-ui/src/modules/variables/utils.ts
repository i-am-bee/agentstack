/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export function maskSecretValue(value: string, visibleChars: number = 3, maskChar: string = '*'): string {
  if (!value || value.length <= visibleChars) {
    return value;
  }

  const maskedLength = value.length - visibleChars;
  const masked = maskChar.repeat(maskedLength);
  const visible = value.slice(-visibleChars);

  return masked + visible;
}
