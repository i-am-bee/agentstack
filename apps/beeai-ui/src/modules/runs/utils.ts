/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

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

export function parseJsonLikeString(string: string): string {
  try {
    const json = JSON5.parse(string);

    if (typeof json === 'string') {
      return json;
    }

    return JSON.stringify(json, null, 2);
  } catch {
    return string;
  }
}
