/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Part } from '@a2a-js/sdk';
import humanizeDuration from 'humanize-duration';
import JSON5 from 'json5';

humanizeDuration.languages.shortEn = {
  h: () => 'h',
  m: () => 'min',
  s: () => 's',
};

export function runDuration(ms: number) {
  const duration = humanizeDuration(ms, {
    units: ['h', 'm', 's'],
    round: true,
    delimiter: ' ',
    spacer: '',
    language: 'shortEn',
  });

  return duration;
}

export const parseJsonLikeString = (string: string): unknown | string => {
  try {
    const json = JSON5.parse(string);

    return json;
  } catch {
    return string;
  }
};

export function extractTextFromParts(parts: Part[]): string {
  const text = parts
    .filter((part) => part.kind === 'text')
    .map((part) => part.text)
    .join('\n');

  return text;
}
