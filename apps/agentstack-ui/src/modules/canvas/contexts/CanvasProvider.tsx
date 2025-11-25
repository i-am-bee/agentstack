/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type PropsWithChildren, useCallback, useEffect, useMemo, useRef, useState } from 'react';

import type { AgentA2AClient } from '#api/a2a/types.ts';
import { useMessages } from '#modules/messages/contexts/Messages/index.ts';
import { UIMessagePartKind } from '#modules/messages/types.ts';
import { isAgentMessage } from '#modules/messages/utils.ts';

import type { CanvasContextValue } from './canvas-context';
import { CanvasContext } from './canvas-context';

interface Props {
  agentClient?: AgentA2AClient;
}

export function CanvasProvider({ agentClient, children }: PropsWithChildren<Props>) {
  const [activeArtifactId, setActiveArtifactId] = useState<string | null>(null);

  const { messages } = useMessages();

  const artifacts = useMemo(() => {
    if (agentClient?.demands.canvasDemands === undefined) {
      return null;
    }

    const artifacts = messages.flatMap((message) =>
      isAgentMessage(message) ? message.parts.filter((part) => part.kind === UIMessagePartKind.Artifact) : [],
    );
    artifacts.reverse();
    return artifacts;
  }, [agentClient?.demands.canvasDemands, messages]);

  const artifactsRef = useRef(artifacts);
  artifactsRef.current = artifacts;

  const getArtifact = useCallback((id: string) => {
    return artifactsRef.current?.find(({ artifactId }) => id === artifactId);
  }, []);

  const lastArtifact = artifacts?.at(-1);

  useEffect(() => {
    setActiveArtifactId(lastArtifact?.artifactId ?? null);
  }, [lastArtifact]);

  const activeArtifact = useMemo(() => {
    if (!activeArtifactId) {
      return null;
    }
    return getArtifact(activeArtifactId) ?? null;
  }, [activeArtifactId, getArtifact]);

  const value = useMemo<CanvasContextValue>(
    () => ({
      artifacts,
      activeArtifact,
      setActiveArtifactId,
      getArtifact,
    }),
    [activeArtifact, artifacts, getArtifact],
  );

  return <CanvasContext.Provider value={value}>{children}</CanvasContext.Provider>;
}
