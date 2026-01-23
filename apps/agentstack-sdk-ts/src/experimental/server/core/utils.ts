/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

interface RetryOptions {
  maxAttempts?: number;
  maxDelayMs?: number;
  shouldAbort?: () => boolean;
  onRetry?: (attempt: number, error: Error, delayMs: number) => void;
}

export async function withRetry<T>(fn: () => Promise<T>, options: RetryOptions = {}): Promise<T> {
  const { maxAttempts = 10, maxDelayMs = 10000, shouldAbort, onRetry } = options;

  let lastError: Error | undefined;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    if (shouldAbort?.()) {
      throw new Error('Operation aborted');
    }

    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      const delay = Math.min(1000 * Math.pow(2, attempt), maxDelayMs);

      onRetry?.(attempt + 1, lastError, delay);

      await sleep(delay);
    }
  }

  throw lastError ?? new Error('Max retry attempts exceeded');
}

export function setsEqual(a: Set<string>, b: Set<string>): boolean {
  if (a.size !== b.size) {
    return false;
  }

  for (const item of a) {
    if (!b.has(item)) {
      return false;
    }
  }

  return true;
}

export function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}
