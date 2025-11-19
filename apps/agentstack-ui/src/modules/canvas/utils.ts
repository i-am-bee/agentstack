/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { v4 as uuid } from 'uuid';

import {
  type UIAgentMessage,
  type UIArtifactPart,
  UIMessagePartKind,
  type UITransformPart,
  UITransformType,
} from '#modules/messages/types.ts';
import { getMessagePartsRawContent, getMessageRawContent } from '#modules/messages/utils.ts';
import { toMarkdownArtifact } from '#utils/markdown.ts';

export function transformArtifactPart(artifactPart: UIArtifactPart, message: UIAgentMessage): UITransformPart {
  const startIndex = getMessageRawContent(message).length;

  const artifactContent = getMessagePartsRawContent(artifactPart.parts);

  const name = artifactPart.name || 'artifact';

  const transformPart: UITransformPart = {
    kind: UIMessagePartKind.Transform,
    id: uuid(),
    type: UITransformType.Artifact,
    startIndex,
    apply: (content, offset) => {
      const adjustedStartIndex = startIndex + offset;
      const before = content.slice(0, adjustedStartIndex);
      const after = content.slice(adjustedStartIndex + artifactContent.length);

      return `${before}${toMarkdownArtifact({ name, content: artifactContent })}${after}`;
    },
  };

  return transformPart;
}
