/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMergeRefs } from '@floating-ui/react';
import clsx from 'clsx';
import { useCallback, useRef } from 'react';

import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import { rehypeSourcePosition } from '#components/MarkdownContent/rehype/rehypeSourcePosition.ts';
import { useToast } from '#contexts/Toast/index.ts';
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
}

export function CanvasMarkdownContent({ className, artifactId, children, enableSelection = true }: Props) {
  const { addToast } = useToast();
  const { submitCanvasEditRequest } = useAgentRun();

  const containerRef = useRef<HTMLDivElement>(null);

  const dialog = useMarkdownSelectionDialog(containerRef);

  const { refs, selection } = dialog;

  const handleEditRequest = useCallback(
    (description: string) => {
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
    },
    [addToast, artifactId, children, selection, submitCanvasEditRequest],
  );

  const containerRefs = useMergeRefs([containerRef, refs.setPositionReference]);

  return (
    <div ref={containerRefs} className={clsx(classes.root, className)}>
      <MarkdownContent rehypePlugins={rehypePlugins}>{children}</MarkdownContent>
      {enableSelection && <Toolbar dialog={dialog} onEditRequest={handleEditRequest} />}
    </div>
  );
}

const rehypePlugins = [rehypeSourcePosition];
