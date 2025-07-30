/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export interface RunAgentFormValues {
  input: string;
  tools?: string[];
}

export interface RunStats {
  startTime?: number;
  endTime?: number;
}
