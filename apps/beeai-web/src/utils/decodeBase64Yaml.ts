/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { parse } from 'yaml';

export function decodeBase64Yaml<T>(base64: string): T {
  return parse(Buffer.from(base64, 'base64').toString('utf-8')) as T;
}
