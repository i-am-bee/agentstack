/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { SourceReference } from '#modules/runs/sources/api/types.ts';

export function createCodeBlock(language: string, snippet: string) {
  return `\`\`\`${language}\n${snippet}\n\`\`\``;
}

export function toMarkdownImage(url: string) {
  return `\n\n![](${url})\n\n`;
}

export function toMarkdownCitation({ text, sources }: { text: string; sources: SourceReference[] }) {
  return `[${text}](citation:${sources.map(({ key }) => key).join(',')})`;
}
