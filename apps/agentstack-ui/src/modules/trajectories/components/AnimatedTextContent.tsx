/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { LineClampText } from '#components/LineClampText/LineClampText.tsx';
import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';

import type { UseAnimatedTextOptions } from '../hooks/useAnimatedText';
import { useAnimatedText } from '../hooks/useAnimatedText';
import { isMarkdown } from '../utils';

interface Props extends UseAnimatedTextOptions {
  children: string;
  className?: string;
  linesClamp?: number;
}

export function AnimatedTextContent({ children, className, linesClamp, ...textOptions }: Props) {
  const displayedText = useAnimatedText({
    ...textOptions,
    text: children,
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
