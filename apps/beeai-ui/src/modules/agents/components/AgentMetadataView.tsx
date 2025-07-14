/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { LogoGithub, Time } from '@carbon/icons-react';
import { SkeletonText } from '@carbon/react';
import clsx from 'clsx';

import type { Agent } from '../api/types';
import { getAgentSourceCodeUrl } from '../utils';
import classes from './AgentMetadataView.module.scss';

interface Props {
  agent: Agent;
  className?: string;
  showSourceCodeLink?: boolean;
}

export function AgentMetadataView({ agent, className, showSourceCodeLink }: Props) {
  const { license, avg_run_time_seconds, avg_run_tokens } = agent.ui;
  const sourceCodeUrl = getAgentSourceCodeUrl(agent);

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

AgentMetadataView.Skeleton = function AgentMetadataSkeleton({ className }: SkeletonProps) {
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
