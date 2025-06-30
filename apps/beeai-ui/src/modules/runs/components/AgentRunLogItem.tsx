/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ChevronDown } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import clsx from 'clsx';
import type { PropsWithChildren } from 'react';
import { useEffect, useRef, useState } from 'react';

import { AnimateHeightChange } from '#components/AnimateHeightChange/AnimateHeightChange.tsx';

import classes from './AgentRunLogItem.module.scss';

export function AgentRunLogItem({ children }: PropsWithChildren) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isClamped, setIsClamped] = useState(false);
  const contentRef = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    const content = contentRef.current;

    if (!content) return;

    const checkContent = () => {
      if (content) {
        setIsClamped(content.scrollWidth > content.clientWidth);
      }
    };

    const observer = new ResizeObserver(checkContent);

    observer.observe(content);

    checkContent();

    return () => observer.disconnect();
  }, [children]);

  return (
    <div className={clsx(classes.root, { [classes.isExpanded]: isExpanded })}>
      <AnimateHeightChange className={classes.holder}>
        <p ref={contentRef} className={clsx(classes.content, { [classes.clamped]: !isExpanded })}>
          {children}
        </p>
      </AnimateHeightChange>

      {(isClamped || isExpanded) && (
        <div className={clsx(classes.toggle, { [classes.toggled]: isExpanded })}>
          <IconButton
            label={isExpanded ? 'Collapse' : 'Expand'}
            kind="ghost"
            size="sm"
            onClick={() => setIsExpanded((expanded) => !expanded)}
          >
            <ChevronDown />
          </IconButton>
        </div>
      )}
    </div>
  );
}
