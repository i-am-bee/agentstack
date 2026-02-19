/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useRef, useState } from 'react';

export enum AnimationStatus {
  Ready = 'ready',
  Animating = 'animating',
  Completed = 'completed',
}

export interface UseAnimatedTextOptions {
  status: AnimationStatus;
  totalDurationMs: number;
  maxAnimatedChars?: number;
  delayMs?: number;
  onAnimationEnd?: () => void;
}

interface UseAnimatedTextProps extends UseAnimatedTextOptions {
  text: string;
}

export function useAnimatedText({
  text,
  status,
  totalDurationMs,
  maxAnimatedChars = DEFAULT_MAX_ANIMATED_CHARS,
  delayMs = 0,
  onAnimationEnd,
}: UseAnimatedTextProps) {
  const shouldAnimate = status === AnimationStatus.Animating && text.length > 0;
  const [displayedText, setDisplayedText] = useState(shouldAnimate ? '' : text);
  const currentIndexRef = useRef<number>(0);

  useEffect(() => {
    if (!shouldAnimate) {
      setDisplayedText(text);
      return;
    }

    const charsToAnimate = Math.min(text.length, maxAnimatedChars);
    const remainingText = text.slice(charsToAnimate);
    const delayPerChar = Math.min(totalDurationMs / charsToAnimate, CHARS_DELAY_MAX_MS);

    let intervalId: NodeJS.Timeout;
    const startAnimation = () => {
      intervalId = setInterval(() => {
        currentIndexRef.current++;

        if (currentIndexRef.current >= charsToAnimate) {
          setDisplayedText(text.slice(0, charsToAnimate) + remainingText);
          clearInterval(intervalId);
        } else {
          setDisplayedText(text.slice(0, currentIndexRef.current));
        }
      }, delayPerChar);
    };

    const timeoutId = setTimeout(startAnimation, delayMs);

    return () => {
      clearTimeout(timeoutId);
      clearInterval(intervalId);
    };
  }, [text, shouldAnimate, totalDurationMs, maxAnimatedChars, delayMs]);

  useEffect(() => {
    if (status === AnimationStatus.Animating && displayedText.length === text.length) {
      onAnimationEnd?.();
    }
  }, [displayedText.length, onAnimationEnd, status, text.length]);

  return displayedText;
}

export const DEFAULT_MAX_ANIMATED_CHARS = 1000;
export const CHARS_DELAY_MAX_MS = 20;
