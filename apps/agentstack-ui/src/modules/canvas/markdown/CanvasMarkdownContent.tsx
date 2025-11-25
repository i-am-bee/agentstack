/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import 'katex/dist/katex.min.css';

import { useMergeRefs } from '@floating-ui/react';
import clsx from 'clsx';
import { useRef } from 'react';

import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';

import classes from './CanvasMarkdownContent.module.scss';
import { useMarkdownSelectionDialog } from './hooks/useMarkdownSelectionDialog';
import { useTextSelection } from './hooks/useTextSelection';
import { Toolbar } from './Toolbar';
import type { MarkdownSelection } from './utils/mapDOMSelectionToMarkdown';
import { mapDOMSelectionToMarkdown } from './utils/mapDOMSelectionToMarkdown';

export interface MarkdownContentProps {
  children?: string;
  className?: string;
  onTextSelected: (selection: MarkdownSelection) => void;
  selectionActionLabel?: string;
  enableSelection?: boolean;
}

export function CanvasMarkdownContent({
  className,
  children,
  onTextSelected,
  enableSelection = true,
}: MarkdownContentProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const selection = useTextSelection(containerRef);

  const dialog = useMarkdownSelectionDialog({ selection, containerRef });

  const handleSelectionAction = () => {
    if (!selection || !onTextSelected || !children) {
      return;
    }

    const { range } = selection;
    const markdownSelection = mapDOMSelectionToMarkdown(range, children);

    if (markdownSelection) {
      onTextSelected(markdownSelection);
    }
  };

  const { refs } = dialog;

  const containerRefs = useMergeRefs([containerRef, refs.setPositionReference]);

  return (
    <div ref={containerRefs} className={clsx(classes.root, className)}>
      <MarkdownContent>{children}</MarkdownContent>
      {enableSelection && <Toolbar dialog={dialog} onAction={handleSelectionAction} />}
    </div>
  );
}
