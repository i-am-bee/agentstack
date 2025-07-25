/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { ArrowUpRight } from '@carbon/icons-react';
import { SkeletonText, Tab, TabList, TabPanel, TabPanels, Tabs } from '@carbon/react';

import { ExternalLink } from '#components/MarkdownContent/components/ExternalLink.tsx';
import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import { SidePanel } from '#components/SidePanel/SidePanel.tsx';
import { useApp } from '#contexts/App/index.ts';
import { SidePanelVariant } from '#contexts/App/types.ts';
import { useAgentNameFromPath } from '#hooks/useAgentNameFromPath.ts';

import { useAgent } from '../api/queries/useAgent';
import { getAgentSourceCodeUrl } from '../utils';
import { AgentCredits } from './AgentCredits';
import classes from './AgentDetailPanel.module.scss';
import { AgentTags } from './AgentTags';
import { AgentTools } from './AgentTools';

export function AgentDetailPanel() {
  const agentName = useAgentNameFromPath();
  const { data: agent, isPending } = useAgent({ name: agentName ?? '' });
  const { activeSidePanel } = useApp();

  if (!agent) return null;

  const {
    description,
    ui: { documentation, contributors, author },
  } = agent;
  const sourceCodeUrl = getAgentSourceCodeUrl(agent);
  const agentInfo = description ?? documentation;

  const isOpen = activeSidePanel === SidePanelVariant.AgentDetail;

  return (
    <SidePanel variant="right" isOpen={isOpen}>
      <div className={classes.tabs}>
        <Tabs>
          <TabList>
            <Tab>Agent details</Tab>

            <Tab>Tools</Tab>
          </TabList>

          <TabPanels>
            <TabPanel>
              <div className={classes.info}>
                {!isPending ? (
                  <>
                    <div className={classes.mainInfo}>
                      {agentInfo && <MarkdownContent className={classes.description}>{agentInfo}</MarkdownContent>}

                      {(author || contributors) && <AgentCredits author={author} contributors={contributors} />}
                    </div>

                    <AgentTags agent={agent} />

                    {sourceCodeUrl && (
                      <ExternalLink href={sourceCodeUrl} className={classes.docsLink}>
                        View source code <ArrowUpRight />
                      </ExternalLink>
                    )}
                  </>
                ) : (
                  <SkeletonText paragraph={true} lineCount={5} />
                )}
              </div>
            </TabPanel>

            <TabPanel>
              <AgentTools agent={agent} />
            </TabPanel>
          </TabPanels>
        </Tabs>
      </div>
    </SidePanel>
  );
}
