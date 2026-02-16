/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMergeRefs } from '@floating-ui/react';
import clsx from 'clsx';
import { useRef } from 'react';

import { rehypeSourcePosition } from '#components/MarkdownContent/rehype/rehypeSourcePosition.ts';
import { useToast } from '#contexts/Toast/index.ts';
import type { UISourcePart } from '#modules/messages/types.ts';
import { ChatMarkdownContent } from '#modules/runs/components/ChatMarkdownContent/ChatMarkdownContent.tsx';
import { useAgentRun } from '#modules/runs/contexts/agent-run/index.ts';

import classes from './CanvasMarkdownContent.module.scss';
import { useMarkdownSelectionDialog } from './hooks/useMarkdownSelectionDialog';
import { Toolbar } from './Toolbar';
import { mapDOMSelectionToMarkdown } from './utils/mapDOMSelectionToMarkdown';

interface Props {
  children?: string;
  artifactId: string;
  className?: string;
  enableSelection?: boolean;
  sources?: UISourcePart[];
}

export function CanvasMarkdownContent({ className, artifactId, children, enableSelection = true, sources }: Props) {
  const { addToast } = useToast();
  const { submitCanvasEditRequest } = useAgentRun();

  const containerRef = useRef<HTMLDivElement>(null);

  const dialog = useMarkdownSelectionDialog(containerRef);

  const { refs, selection } = dialog;

  const handleEditRequest = (description: string) => {
    if (!selection || !children) {
      return;
    }

    try {
      const markdownSelection = mapDOMSelectionToMarkdown(selection.range, children);

      if (markdownSelection) {
        submitCanvasEditRequest({
          ...markdownSelection,
          description,
          artifactId,
        });
      }
    } catch (error) {
      addToast({
        kind: 'error',
        title: 'Error submitting edit request',
        message: 'An error occurred while processing your selection. Please try again.',
      });

      console.error('Error submitting canvas edit request:', error);

      return;
    }
  };

  const containerRefs = useMergeRefs([containerRef, refs.setPositionReference]);

  return (
    <div ref={containerRefs} className={clsx(classes.root, className)}>
      <ChatMarkdownContent rehypePlugins={rehypePlugins} sources={sources}>
        {children}
      </ChatMarkdownContent>
      {enableSelection && <Toolbar dialog={dialog} onEditRequest={handleEditRequest} />}
    </div>
  );
}

const rehypePlugins = [rehypeSourcePosition];
