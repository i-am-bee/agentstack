/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import type { UISourcePart } from '#modules/messages/types.ts';

import { useAgentRun } from '../contexts/agent-run';
import classes from './MessageContent.module.scss';

interface Props {
  content: string;
  sources: UISourcePart[];
}

export function MessageContent({ content, sources }: Props) {
  const { isPending } = useAgentRun();

  return content ? (
    <MarkdownContent sources={sources} isPending={isPending}>
      {content}
    </MarkdownContent>
  ) : (
    <div className={classes.empty}>Message has no content</div>
  );
}
