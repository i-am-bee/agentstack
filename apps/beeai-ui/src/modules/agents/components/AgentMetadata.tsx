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

import { LogoGithub, Time } from '@carbon/icons-react';
import { SkeletonText } from '@carbon/react';
import clsx from 'clsx';

import type { Agent } from '../api/types';
import { getAgentSourceCodeUrl, getAgentStatusMetadata } from '../utils';
import classes from './AgentMetadata.module.scss';

interface Props {
  agent: Agent;
  className?: string;
  showSourceCodeLink?: boolean;
}

export function AgentMetadata({ agent, className, showSourceCodeLink }: Props) {
  const { license } = agent.metadata;
  const sourceCodeUrl = getAgentSourceCodeUrl(agent);
  const { avg_run_time_seconds, avg_run_tokens } = getAgentStatusMetadata({
    agent,
    keys: ['avg_run_time_seconds', 'avg_run_tokens'],
  });

  const hasSourceCodeLinkVisible = showSourceCodeLink && sourceCodeUrl;
  if (!avg_run_time_seconds || !avg_run_tokens || !license || !hasSourceCodeLinkVisible) {
    return null;
  }

  return (
    <ul className={clsx(classes.root, className)}>
      {avg_run_time_seconds && (
        <li className={classes.item}>
          <Time />
          {avg_run_time_seconds}s/run (avg)
        </li>
      )}
      {avg_run_tokens && <li className={classes.item}>{avg_run_tokens} tokens/run (avg)</li>}

      {license && <li className={classes.item}>{license}</li>}

      {hasSourceCodeLinkVisible && (
        <li className={classes.item}>
          <SourceCodeLink url={sourceCodeUrl} />
        </li>
      )}
    </ul>
  );
}

interface SkeletonProps {
  className?: string;
}

AgentMetadata.Skeleton = function AgentMetadataSkeleton({ className }: SkeletonProps) {
  return <SkeletonText className={clsx(classes.root, className)} width="33%" />;
};

function SourceCodeLink({ url }: { url: string }) {
  return (
    <a
      target="_blank"
      rel="noreferrer"
      href={url}
      className={classes.sourceCodeLink}
      aria-label="View source code on Github"
    >
      <LogoGithub size={16} />

      <span>View code</span>
    </a>
  );
}
