/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { LineClampText } from '#components/LineClampText/LineClampText.tsx';
import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';

import { useAnimatedText } from '../hooks/useAnimatedText';
import { isMarkdown } from '../utils';

interface Props {
  children: string;
  className?: string;
  totalDurationMs: number;
  maxAnimatedChars?: number;
  shouldAnimate?: boolean;
  linesClamp?: number;
}

export function AnimatedTextContent({
  children,
  className,
  shouldAnimate,
  totalDurationMs,
  maxAnimatedChars,
  linesClamp,
}: Props) {
  const displayedText = useAnimatedText({
    text: children,
    shouldAnimate,
    totalDurationMs,
    maxAnimatedChars,
  });

  const contentIsMarkdown = useMemo(() => isMarkdown(children), [children]);

  if (linesClamp && displayedText.length > 0) {
    return (
      <LineClampText lines={linesClamp} useBlockElement={contentIsMarkdown} className={className}>
        {contentIsMarkdown ? <MarkdownContent>{displayedText}</MarkdownContent> : displayedText}
      </LineClampText>
    );
  }

  const Component = contentIsMarkdown ? MarkdownContent : 'div';
  return <Component className={className}>{displayedText}</Component>;
}
