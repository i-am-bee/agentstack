/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { CanvasFulfillments } from 'agentstack-sdk';

import type { UICanvasEditRequestParams } from '#modules/canvas/types.ts';

export function getCanvasEditRequestFulfillment({
  startIndex,
  endIndex,
  artifactId,
  description,
}: UICanvasEditRequestParams): CanvasFulfillments {
  return {
    start_index: startIndex,
    end_index: endIndex,
    artifact_id: artifactId,
    description,
  };
}
