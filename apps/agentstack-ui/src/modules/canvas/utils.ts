/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { CanvasEditRequest } from 'agentstack-sdk';
import { v4 as uuid } from 'uuid';

import type { UIMessagePart } from '#modules/messages/types.ts';
import {
  type UIAgentMessage,
  type UIArtifactPart,
  UIMessagePartKind,
  type UITransformPart,
  UITransformType,
} from '#modules/messages/types.ts';
import { getMessagePartsRawContent, getMessageRawContent, sortMessageParts } from '#modules/messages/utils.ts';
import { getSourceTransformPart } from '#modules/sources/utils.ts';
import { findWithIndex } from '#utils/helpers.ts';
import { toMarkdownArtifact } from '#utils/markdown.ts';

import type { UICanvasEditRequestParams } from './types';

type ArtifactPartUpdate = {
  index: number;
  part: UIMessagePart;
};

type ProcessArtifactResult = {
  add?: UIMessagePart[];
  update?: ArtifactPartUpdate[];
};

export function getArtifactPartUpdates(
  part: UIArtifactPart,
  existingParts: UIMessagePart[],
  message: UIAgentMessage,
): ProcessArtifactResult {
  const { artifactId, parts } = part;

  const sourceParts = parts
    .filter((p) => p.kind === UIMessagePartKind.Source)
    .map((sourcePart) => ({ ...sourcePart, artifactId }));
  const sourceTransformParts = sourceParts.map((sourcePart) => getSourceTransformPart(sourcePart));

  const partsWithTransforms = [
    ...parts.filter((p) => p.kind !== UIMessagePartKind.Source),
    ...sourceParts,
    ...sourceTransformParts,
  ];
  const partWithTransforms: UIArtifactPart = { ...part, parts: sortMessageParts(partsWithTransforms) };

  const [existingArtifactIndex, existingArtifactPart] = findWithIndex(
    existingParts,
    (existingPart) => existingPart.kind === UIMessagePartKind.Artifact && existingPart.artifactId === artifactId,
  );

  if (existingArtifactPart && existingArtifactPart.kind === UIMessagePartKind.Artifact) {
    const updatedArtifactPart: UIArtifactPart = {
      ...existingArtifactPart,
      parts: sortMessageParts([...existingArtifactPart.parts, ...partsWithTransforms]),
    };

    const [existingTransformIndex, existingTransformPart] = findWithIndex(
      existingParts,
      (existingPart) =>
        existingPart.kind === UIMessagePartKind.Transform &&
        existingPart.type === UITransformType.Artifact &&
        existingPart.artifactId === artifactId,
    );

    if (!existingTransformPart || existingTransformPart.kind !== UIMessagePartKind.Transform) {
      console.error('Artifact is in illegal state: missing corresponding transform part');
      const transformPart = getArtifactTransformPart(partWithTransforms, message);
      return {
        add: [partWithTransforms, transformPart],
      };
    }

    const updatedTransformPart = updateArtifactTransformPart(existingTransformPart, updatedArtifactPart);

    return {
      update: [
        { index: existingArtifactIndex, part: updatedArtifactPart },
        { index: existingTransformIndex, part: updatedTransformPart },
      ],
    };
  } else {
    const transformPart = getArtifactTransformPart(partWithTransforms, message);
    return {
      add: [partWithTransforms, transformPart],
    };
  }
}

function getArtifactTransformPart(artifactPart: UIArtifactPart, message: UIAgentMessage): UITransformPart {
  const startIndex = getMessageRawContent(message).length;

  const artifactContent = getMessagePartsRawContent(artifactPart.parts);

  const { artifactId, name } = artifactPart;

  const transformPart: UITransformPart = {
    kind: UIMessagePartKind.Transform,
    id: uuid(),
    type: UITransformType.Artifact,
    artifactId,
    startIndex,
    apply: (content, offset) => {
      const adjustedStartIndex = startIndex + offset;
      const before = content.slice(0, adjustedStartIndex);
      const after = content.slice(adjustedStartIndex + artifactContent.length);

      return `${before}${toMarkdownArtifact({ id: artifactId, name })}${after}`;
    },
  };

  return transformPart;
}

function updateArtifactTransformPart(transformPart: UITransformPart, artifactPart: UIArtifactPart): UITransformPart {
  const artifactContent = getMessagePartsRawContent(artifactPart.parts);

  const { artifactId, name } = artifactPart;

  const newTransformPart = { ...transformPart };
  newTransformPart.apply = (content, offset) => {
    const adjustedStartIndex = newTransformPart.startIndex + offset;
    const before = content.slice(0, adjustedStartIndex);
    const after = content.slice(adjustedStartIndex + artifactContent.length);

    return `${before}${toMarkdownArtifact({ id: artifactId, name })}${after}`;
  };

  return newTransformPart;
}

export function getCanvasEditRequest({
  startIndex,
  endIndex,
  artifactId,
  description,
}: UICanvasEditRequestParams): CanvasEditRequest {
  return {
    start_index: startIndex,
    end_index: endIndex,
    artifact_id: artifactId,
    description,
  };
}
