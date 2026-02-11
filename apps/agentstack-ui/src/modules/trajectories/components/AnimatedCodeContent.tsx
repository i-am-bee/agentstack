/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CodeSnippet } from '#components/CodeSnippet/CodeSnippet.tsx';

import type { UseAnimatedTextOptions } from '../hooks/useAnimatedText';
import { useAnimatedText } from '../hooks/useAnimatedText';

interface Props extends UseAnimatedTextOptions {
  children: string;
}

export function AnimatedCodeContent({ children, ...textOptions }: Props) {
  const displayedText = useAnimatedText({
    ...textOptions,
    text: children,
  });

  return (
    <CodeSnippet canCopy withBorder>
      {displayedText}
    </CodeSnippet>
  );
}
