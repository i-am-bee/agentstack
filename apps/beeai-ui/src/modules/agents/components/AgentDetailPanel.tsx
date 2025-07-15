/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { ArrowUpRight } from '@carbon/icons-react';
import { SkeletonText, Tab, TabList, TabPanel, TabPanels, Tabs } from '@carbon/react';

import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import { SidePanel } from '#components/SidePanel/SidePanel.tsx';
import { useApp } from '#contexts/App/index.ts';
import { SidePanelVariant } from '#contexts/App/types.ts';
import { useAgentNameFromPath } from '#hooks/useAgentNameFromPath.ts';

import { useAgent } from '../api/queries/useAgent';
import classes from './AgentDetailPanel.module.scss';
import { AgentTools } from './AgentTools';

export function AgentDetailPanel() {
  const agentName = useAgentNameFromPath();
  const { data: agent, isPending } = useAgent({ name: agentName ?? '' });
  const { activeSidePanel } = useApp();

  if (!agent) return null;

  // TODO: a2a
  // const { description, metadata } = agent;
  // const agentUrl = getAvailableAgentLinkUrl(metadata, ['homepage', 'documentation', 'source-code']);
  // const authorName = metadata.author?.name;
  // const agentInfo = description ?? metadata.documentation;
  const agentInfo = agent.description;
  const authorName = undefined;
  const agentUrl = undefined;

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
                    {(agentInfo || authorName) && (
                      <div className={classes.infoHeader}>
                        {agentInfo && <MarkdownContent className={classes.description}>{agentInfo}</MarkdownContent>}

                        {authorName && <p className={classes.author}>By {authorName}</p>}
                      </div>
                    )}

                    {/* TODO: a2a <AgentTags agent={agent} /> */}

                    {agentUrl && (
                      <a href={agentUrl} target="_blank" rel="noreferrer" className={classes.docsLink}>
                        View more <ArrowUpRight />
                      </a>
                    )}
                  </>
                ) : (
                  <>
                    <SkeletonText paragraph={true} lineCount={5} />
                  </>
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
