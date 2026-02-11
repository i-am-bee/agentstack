/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useState } from 'react';

export interface UseAnimatedTextOptions {
  shouldAnimate?: boolean;
  totalDurationMs: number;
  maxAnimatedChars?: number;
  delayMs?: number;
}

interface UseAnimatedTextProps extends UseAnimatedTextOptions {
  text: string;
}

export function useAnimatedText({
  text,
  shouldAnimate: shouldAnimateProp = true,
  totalDurationMs,
  maxAnimatedChars = DEFAULT_MAX_ANIMATED_CHARS,
  delayMs = 0,
}: UseAnimatedTextProps) {
  const shouldAnimate = shouldAnimateProp && text.length > 0;
  const [displayedText, setDisplayedText] = useState(shouldAnimate ? '' : text);

  useEffect(() => {
    const charsToAnimate = Math.min(text.length, maxAnimatedChars);
    if (!shouldAnimate || charsToAnimate === 0) {
      setDisplayedText(text);
      return;
    }

    const remainingText = text.slice(charsToAnimate);
    const delayPerChar = Math.min(totalDurationMs / charsToAnimate, CHARS_DELAY_MAX_MS);

    let intervalId: NodeJS.Timeout;
    const startAnimation = () => {
      let currentIndex = 0;
      intervalId = setInterval(() => {
        currentIndex++;

        if (currentIndex >= charsToAnimate) {
          setDisplayedText(text.slice(0, charsToAnimate) + remainingText);
          clearInterval(intervalId);
        } else {
          setDisplayedText(text.slice(0, currentIndex));
        }
      }, delayPerChar);
    };

    const timeoutId = setTimeout(startAnimation, delayMs);

    return () => {
      clearTimeout(timeoutId);
      clearInterval(intervalId);
    };
  }, [text, shouldAnimate, totalDurationMs, maxAnimatedChars, delayMs]);

  return displayedText;
}

const DEFAULT_MAX_ANIMATED_CHARS = 1000;
export const CHARS_DELAY_MAX_MS = 20;
