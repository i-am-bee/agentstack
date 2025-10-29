/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export async function* readableToAsyncIterable<T>(stream?: ReadableStream<T>): AsyncIterable<T> {
  if (!stream) {
    return;
  }

  const reader = stream.getReader();

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        return;
      }

      yield value;
    }
  } finally {
    reader.releaseLock();
  }
}
