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
  parsed?: unknown;
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
      parsed: maybeJson,
    };
  } catch {
    return {
      type: 'string',
      value: content,
    };
  }
}

export function getRunParamsFromUrl(pathname: string) {
  // Parse parameters from pathname: /run/[providerId]/c/[contextId] or /run/[providerId]
  // because useParams does not react to changes in the URL via history.pushState
  const match = pathname.match(/^\/run\/([^/]+)(?:\/c\/([^/]+))?/);

  const providerId = match?.at(1);
  const contextId = match?.at(2);

  return {
    providerId,
    contextId,
  };
}
