/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import humanizeDuration from 'humanize-duration';
import JSON5 from 'json5';

import { isNotNull } from '#utils/helpers.ts';

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

function parseJsonLikeString(string: string): unknown {
  try {
    const json = JSON5.parse(string);

    return json;
  } catch {
    return string;
  }
}

interface MaybeParsedJson {
  type: 'string' | 'json';
  value: string;
}

export function maybeParseJson(content: string | null | undefined): MaybeParsedJson | null {
  if (!isNotNull(content)) {
    return null;
  }

  const maybeJson = parseJsonLikeString(content);

  if (typeof maybeJson === 'string') {
    return {
      type: 'string',
      value: maybeJson,
    };
  }

  try {
    const json = JSON.stringify(maybeJson, null, 2);

    return {
      type: 'json',
      value: json,
    };
  } catch {
    return {
      type: 'string',
      value: content,
    };
  }
}
