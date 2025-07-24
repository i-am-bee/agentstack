/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { LogoGithub } from '@carbon/icons-react';
import { SkeletonText } from '@carbon/react';
import clsx from 'clsx';

import type { Agent } from '../api/types';
import classes from './AgentMetadataView.module.scss';

interface Props {
  agent: Agent;
  className?: string;
  showSourceCodeLink?: boolean;
}

export function AgentMetadataView({ agent, className, showSourceCodeLink }: Props) {
  const { license, source_code_url } = agent.ui;

  const hasSourceCodeLinkVisible = showSourceCodeLink && source_code_url;
  if (!(license || hasSourceCodeLinkVisible)) {
    return null;
  }

  return (
    <ul className={clsx(classes.root, className)}>
      {/* TODO: to be replaced with real metrics
      {avg_run_time_seconds && (
        <li className={classes.item}>
          <Time />
          {avg_run_time_seconds}s/run (avg)
        </li>
      )}
      {avg_run_tokens && <li className={classes.item}>{avg_run_tokens} tokens/run (avg)</li>} */}

      {license && <li className={classes.item}>{license}</li>}

      {hasSourceCodeLinkVisible && (
        <li className={classes.item}>
          <SourceCodeLink url={source_code_url} />
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
