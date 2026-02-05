/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useMemo, useState } from 'react';

import { LineClampText } from '#components/LineClampText/LineClampText.tsx';
import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';

import { isMarkdown } from '../utils';

interface Props {
  children: string;
  className?: string;
  totalDurationMs?: number;
  maxAnimatedChars?: number;
  shouldAnimate?: boolean;
  lineClamp?: {
    lines: number;
    useBlockElement?: boolean;
  };
}

const DEFAULT_TOTAL_DURATION_MS = 1500;
const DEFAULT_MAX_ANIMATED_CHARS = 500;
const CHARS_DELAY_MAX_MS = 20;

export function AnimatedText({
  children,
  className,
  shouldAnimate: shouldAnimateProp = true,
  totalDurationMs = DEFAULT_TOTAL_DURATION_MS,
  maxAnimatedChars = DEFAULT_MAX_ANIMATED_CHARS,
  lineClamp,
}: Props) {
  const shouldAnimate = shouldAnimateProp && children.length > 0;
  const [displayedText, setDisplayedText] = useState(shouldAnimate ? '' : children);

  const contentIsMarkdown = useMemo(() => isMarkdown(children), [children]);

  useEffect(() => {
    if (!shouldAnimate) {
      setDisplayedText(children);
      return;
    }

    const charsToAnimate = Math.min(children.length, maxAnimatedChars);
    const remainingText = children.slice(charsToAnimate);

    const delayPerChar = Math.min(totalDurationMs / charsToAnimate, CHARS_DELAY_MAX_MS);

    let currentIndex = 0;
    const intervalId = setInterval(() => {
      currentIndex++;

      if (currentIndex >= charsToAnimate) {
        setDisplayedText(children.slice(0, charsToAnimate) + remainingText);
        clearInterval(intervalId);
      } else {
        setDisplayedText(children.slice(0, currentIndex));
      }
    }, delayPerChar);

    return () => {
      clearInterval(intervalId);
    };
  }, [children, shouldAnimate, totalDurationMs, maxAnimatedChars]);

  if (lineClamp && displayedText.length > 0) {
    const { useBlockElement, lines } = lineClamp;

    return (
      <LineClampText lines={lines} useBlockElement={useBlockElement} className={className}>
        {contentIsMarkdown ? <MarkdownContent>{displayedText}</MarkdownContent> : displayedText}
      </LineClampText>
    );
  }

  const Component = contentIsMarkdown ? MarkdownContent : 'div';
  return <Component className={className}>{displayedText}</Component>;
}
