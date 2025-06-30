/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export async function ensureResponse<T>({
  response,
  errorContext,
  resolveAs = 'json',
}: {
  response: Response;
  errorContext: string;
  resolveAs?: 'json' | 'text';
}) {
  if (!response.ok) {
    throw new Error(`Failed to fetch ${errorContext}: ${response.status}, ${await response.text()}`);
  }

  return response[resolveAs]() as T;
}
