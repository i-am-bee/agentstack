/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { AnimatePresence, motion } from 'framer-motion';

import { Container } from '#components/layouts/Container.tsx';
import { MainContent } from '#components/layouts/MainContent.tsx';
import { ViewHeader } from '#components/ViewHeader/ViewHeader.tsx';
import { ViewStack } from '#components/ViewStack/ViewStack.tsx';
import type { Agent } from '#modules/agents/api/types.ts';
import { PlatformContextProvider } from '#modules/platform-context/contexts/PlatformContextProvider.tsx';
import { useEnsurePlatformContext } from '#modules/platform-context/hooks/useEnsurePlatformContext.ts';
import { A2AClientProvider } from '#modules/runs/contexts/a2a-client/A2AClientProvider.tsx';
import { AgentSecretsProvider } from '#modules/runs/contexts/agent-secrets/AgentSecretsProvider.tsx';

import { agentDetailFadeProps } from './AgentDetailView';
import { AgentSecrets } from './AgentSecrets';
import { AgentSection } from './AgentSection';

interface Props {
  agent: Agent;
}

export function AgentSettingsView({ agent }: Props) {
  return (
    <PlatformContextProvider>
      <AgentSettingsViewWithContext agent={agent} />
    </PlatformContextProvider>
  );
}

function AgentSettingsViewWithContext({ agent }: Props) {
  useEnsurePlatformContext(agent);

  return (
    <A2AClientProvider agent={agent}>
      <AgentSecretsProvider agent={agent}>
        <MainContent>
          <Container size="sm">
            <ViewStack>
              <AnimatePresence>
                <motion.div {...agentDetailFadeProps} key="header">
                  <ViewHeader heading="Agent settings" />
                </motion.div>

                <motion.div {...agentDetailFadeProps} key="secrets">
                  <AgentSection title="Secrets">
                    <AgentSecrets />
                  </AgentSection>
                </motion.div>
              </AnimatePresence>
            </ViewStack>
          </Container>
        </MainContent>
      </AgentSecretsProvider>
    </A2AClientProvider>
  );
}
