/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { SkeletonText, Tab, TabList, TabPanel, TabPanels, Tabs } from '@carbon/react';

import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import { SidePanel } from '#components/SidePanel/SidePanel.tsx';
import { useApp } from '#contexts/App/index.ts';
import { SidePanelVariant } from '#contexts/App/types.ts';
import { useParamsFromUrl } from '#hooks/useParamsFromUrl.ts';
import { useAgent } from '#modules/agents/api/queries/useAgent.ts';

import { AgentCredits } from './AgentCredits';
import classes from './AgentDetailPanel.module.scss';
import { AgentSecrets } from './AgentSecrets';
import { AgentTags } from './AgentTags';
import { AgentToolsList } from './AgentToolsList';

export function AgentDetailPanel() {
  const { providerId } = useParamsFromUrl();
  const { data: agent, isPending } = useAgent({ providerId: providerId ?? '' });
  const { activeSidePanel } = useApp();

  if (!agent) return null;

  const {
    description,
    ui: { contributors, author },
  } = agent;

  const isOpen = activeSidePanel === SidePanelVariant.AgentDetail;

  return (
    <SidePanel isOpen={isOpen} showCloseButton>
      <div className={classes.tabs}>
        <Tabs>
          <TabList>
            <Tab>Agent details</Tab>
            <Tab>Tools</Tab>
            <Tab>Secrets</Tab>
          </TabList>

          <TabPanels>
            <TabPanel>
              <div className={classes.info}>
                {!isPending ? (
                  <>
                    <div className={classes.mainInfo}>
                      {description && <MarkdownContent className={classes.description}>{description}</MarkdownContent>}

                      {(author || contributors) && <AgentCredits author={author} contributors={contributors} />}
                    </div>

                    <AgentTags agent={agent} />
                  </>
                ) : (
                  <SkeletonText paragraph lineCount={5} />
                )}
              </div>
            </TabPanel>

            <TabPanel>
              <AgentToolsList agent={agent} />
            </TabPanel>
            <TabPanel>
              <AgentSecrets />
            </TabPanel>
          </TabPanels>
        </Tabs>
      </div>
    </SidePanel>
  );
}
