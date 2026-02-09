/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CodeSnippet } from '#components/CodeSnippet/CodeSnippet.tsx';

import { useAnimatedText } from '../hooks/useAnimatedText';

interface Props {
  children: string;
  totalDurationMs: number;
  maxAnimatedChars?: number;
  shouldAnimate?: boolean;
}

export function AnimatedCodeContent({ children, shouldAnimate, totalDurationMs, maxAnimatedChars }: Props) {
  const displayedText = useAnimatedText({
    text: children,
    shouldAnimate,
    totalDurationMs,
    maxAnimatedChars,
  });

  return (
    <CodeSnippet canCopy withBorder>
      {displayedText}
    </CodeSnippet>
  );
}
