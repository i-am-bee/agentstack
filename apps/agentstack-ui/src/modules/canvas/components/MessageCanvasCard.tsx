/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCanvas } from '../contexts';
import { CanvasCard } from './CanvasCard';
import classes from './MessageCanvasCard.module.scss';

export interface MessageCanvasCardProps {
  name?: string;
  artifactId: string;
}

export function MessageCanvasCard({ name, artifactId }: MessageCanvasCardProps) {
  const { setActiveArtifactId, activeArtifact } = useCanvas();

  return (
    <CanvasCard
      className={classes.root}
      heading={name}
      isActive={activeArtifact?.artifactId === artifactId}
      onClick={() => setActiveArtifactId(artifactId)}
    />
  );
}
