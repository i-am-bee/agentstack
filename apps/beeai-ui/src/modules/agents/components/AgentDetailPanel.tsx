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
import { TransitionLink } from '#components/TransitionLink/TransitionLink.tsx';
import { useApp } from '#contexts/App/index.ts';
import { routes } from '#utils/router.ts';

import { useAgent } from '../api/queries/useAgent';
import type { AgentPageParams } from '../types';
import classes from './AgentDetailPanel.module.scss';
import { AgentMetadata } from './AgentMetadata';
import { AgentTags } from './AgentTags';

export function AgentDetailPanel() {
  const { agentName } = useParams<AgentPageParams>();
  const { data: agent, isPending } = useAgent({ name: agentName ?? '' });
  const { agentDetailOpen } = useApp();

  if (!agent) return null;

  const { name, description } = agent;

  return agent ? (
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
                  {description && <MarkdownContent className={classes.description}>{description}</MarkdownContent>}

                  <AgentMetadata agent={agent} />

                  <AgentTags agent={agent} />

                  <TransitionLink href={routes.agentDetail({ name })} className={classes.detailLink}>
                    View more <ArrowUpRight />
                  </TransitionLink>
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
  ) : null;
}
