/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PhrasingContent } from 'mdast';
import { remark } from 'remark';

import type { UITrajectoryPart } from '#modules/messages/types.ts';
import { isNotNull } from '#utils/helpers.ts';

import { NON_VIEWABLE_TRAJECTORY_PROPERTIES } from './constants';
import type { NonViewableTrajectoryProperty } from './types';

export function hasViewableTrajectoryParts(trajectory: UITrajectoryPart) {
  return Object.entries(trajectory)
    .filter(([key]) => !NON_VIEWABLE_TRAJECTORY_PROPERTIES.includes(key as NonViewableTrajectoryProperty))
    .some(([, value]) => isNotNull(value));
}

export function isMarkdown(maybeMarkdown: string): boolean {
  try {
    const result = remark.parse(maybeMarkdown);

    // If there's a single paragraph with only text nodes, it's plain text (not markdown)
    if (result.children.length === 1 && result.children[0].type === 'paragraph') {
      const paragraph = result.children[0];
      const hasOnlyText = paragraph.children.every((child: PhrasingContent) => child.type === 'text');
      return !hasOnlyText;
    }

    return true;
  } catch {
    return true;
  }
}
