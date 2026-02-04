/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PhrasingContent, Root } from 'mdast';
import { useEffect, useMemo, useState } from 'react';
import { remark } from 'remark';

import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';

interface Props {
  children: string;
  className?: string;
  totalDurationMs?: number;
  maxAnimatedChars?: number;
}

const DEFAULT_TOTAL_DURATION_MS = 1500;
const DEFAULT_MAX_ANIMATED_CHARS = 255;

/**
 * Check if markdown content has any actual formatting.
 * Returns true if the content is just plain text (no formatting).
 */
function isPlainText(markdown: string): boolean {
  try {
    const ast = remark.parse(markdown) as Root;

    // Check if AST contains only plain text
    // If there's a single paragraph with only text nodes, it's plain text
    if (ast.children.length === 1 && ast.children[0].type === 'paragraph') {
      const paragraph = ast.children[0];
      const hasOnlyText = paragraph.children.every((child: PhrasingContent) => child.type === 'text');
      return hasOnlyText;
    }

    // Multiple paragraphs or other nodes = has formatting
    return false;
  } catch {
    // If parsing fails, assume it has formatting to be safe
    return false;
  }
}

export function AnimatedMarkdown({
  children,
  className,
  totalDurationMs = DEFAULT_TOTAL_DURATION_MS,
  maxAnimatedChars = DEFAULT_MAX_ANIMATED_CHARS,
}: Props) {
  const [displayedText, setDisplayedText] = useState('');

  // Check if content is plain text (no markdown formatting)
  const contentIsPlainText = useMemo(() => isPlainText(children), [children]);
  const shouldAnimate = children.length > 0;

  useEffect(() => {
    if (!shouldAnimate) {
      setDisplayedText(children);
      return;
    }

    // Determine how many characters to animate
    const charsToAnimate = Math.min(children.length, maxAnimatedChars);
    const remainingText = children.slice(charsToAnimate);

    // Calculate delay between characters to fit total duration
    const delayPerChar = totalDurationMs / charsToAnimate;

    let currentIndex = 0;
    const intervalId = setInterval(() => {
      currentIndex++;

      if (currentIndex >= charsToAnimate) {
        // Animation complete - add remaining text
        setDisplayedText(children.slice(0, charsToAnimate) + remainingText);
        clearInterval(intervalId);
      } else {
        // Still animating - only show animated portion
        setDisplayedText(children.slice(0, currentIndex));
      }
    }, delayPerChar);

    return () => clearInterval(intervalId);
  }, [children, shouldAnimate, totalDurationMs, maxAnimatedChars]);

  if (contentIsPlainText) {
    return <div className={className}>{displayedText}</div>;
  }

  // Always render with MarkdownContent for consistent styling
  return <MarkdownContent className={className}>{displayedText}</MarkdownContent>;
}
