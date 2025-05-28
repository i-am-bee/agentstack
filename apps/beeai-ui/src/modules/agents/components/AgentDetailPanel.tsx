/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { ArrowUpRight } from '@carbon/icons-react';
import { SkeletonText, Tab, TabList, TabPanel, TabPanels, Tabs } from '@carbon/react';
import { useParams } from 'react-router';

import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import { SidePanel } from '#components/SidePanel/SidePanel.tsx';
import { useApp } from '#contexts/App/index.ts';

import { useAgent } from '../api/queries/useAgent';
import type { AgentPageParams } from '../types';
import { getAvailableAgentLinkUrl } from '../utils';
import classes from './AgentDetailPanel.module.scss';
import { AgentTags } from './AgentTags';

export function AgentDetailPanel() {
  const { agentName } = useParams<AgentPageParams>();
  const { data: agent, isPending } = useAgent({ name: agentName ?? '' });
  const { agentDetailOpen } = useApp();

  if (!agent) return null;

  const { description, metadata } = agent;
  const agentUrl = getAvailableAgentLinkUrl(metadata, ['homepage', 'documentation', 'source-code']);
  const authorName = metadata.author?.name;
  const agentInfo = description ?? metadata.documentation;

  return (
    <SidePanel variant="right" isOpen={agentDetailOpen}>
      <div className={classes.tabs}>
        <Tabs>
          <TabList>
            <Tab>Agent details</Tab>

            <Tab disabled>Tools</Tab>
          </TabList>

          <TabPanels>
            <TabPanel className={classes.info}>
              {!isPending ? (
                <>
                  {agentInfo && <MarkdownContent className={classes.description}>{agentInfo}</MarkdownContent>}

                  {authorName && <span>By {authorName}</span>}

                  <AgentTags agent={agent} />

                  {agentUrl && (
                    <a href={agentUrl} rel="noreferrer" className={classes.docsLink}>
                      View more <ArrowUpRight />
                    </a>
                  )}
                </>
              ) : (
                <>
                  <SkeletonText paragraph={true} lineCount={5} />
                </>
              )}
            </TabPanel>
          </TabPanels>
        </Tabs>
      </div>
    </SidePanel>
  );
}
