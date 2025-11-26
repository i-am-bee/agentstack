/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMergeRefs } from '@floating-ui/react';
import clsx from 'clsx';
import { useRef } from 'react';

import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import { rehypeSourcePosition } from '#components/MarkdownContent/rehype/rehypeSourcePosition.ts';
import { useAgentRun } from '#modules/runs/contexts/agent-run/index.ts';

import classes from './CanvasMarkdownContent.module.scss';
import { useMarkdownSelectionDialog } from './hooks/useMarkdownSelectionDialog';
import { Toolbar } from './Toolbar';
import { mapDOMSelectionToMarkdown } from './utils/mapDOMSelectionToMarkdown';

export interface MarkdownContentProps {
  children?: string;
  artifactId: string;
  className?: string;
  selectionActionLabel?: string;
  enableSelection?: boolean;
}

export function CanvasMarkdownContent({
  className,
  artifactId,
  children,
  enableSelection = true,
}: MarkdownContentProps) {
  const { submitCanvasEditRequest } = useAgentRun();

  const containerRef = useRef<HTMLDivElement>(null);

  const dialog = useMarkdownSelectionDialog(containerRef);

  const { refs, selection } = dialog;

  const handleEditRequest = (description: string) => {
    if (!selection || !children) {
      return;
    }

    const markdownSelection = mapDOMSelectionToMarkdown(selection.range, children);

    if (markdownSelection) {
      submitCanvasEditRequest({
        ...markdownSelection,
        description,
        artifactId,
      });
    }
  };

  const containerRefs = useMergeRefs([containerRef, refs.setPositionReference]);

  return (
    <div ref={containerRefs} className={clsx(classes.root, className)}>
      <MarkdownContent rehypePlugins={rehypePlugins}>{children}</MarkdownContent>
      {enableSelection && <Toolbar dialog={dialog} onEditRequest={handleEditRequest} />}
    </div>
  );
}

const rehypePlugins = [rehypeSourcePosition];
