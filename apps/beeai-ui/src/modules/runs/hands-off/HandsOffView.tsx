/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { MainContent } from '#components/layouts/MainContent.tsx';
import type { Agent } from '#modules/agents/api/types.ts';

import { useHandsOff } from '../contexts/hands-off';
import { HandsOffProvider } from '../contexts/hands-off/HandsOffProvider';
import { FileUploadProvider } from '../files/contexts/FileUploadProvider';
import { SourcesPanel } from '../sources/components/SourcesPanel';
import { HandsOffLandingView } from './HandsOffLandingView';
import { HandsOffOutputView } from './HandsOffOutputView';

interface Props {
  agent: Agent;
}

export function HandsOffView({ agent }: Props) {
  return (
    <FileUploadProvider key={agent.name}>
      <HandsOffProvider agent={agent}>
        <HandsOff />
      </HandsOffProvider>
    </FileUploadProvider>
  );
}

function HandsOff() {
  const { output, isPending } = useHandsOff();

  const isIdle = !isPending && !output;

  return (
    <>
      <MainContent spacing="md">{isIdle ? <HandsOffLandingView /> : <HandsOffOutputView />}</MainContent>

      <SourcesPanel />
    </>
  );
}
