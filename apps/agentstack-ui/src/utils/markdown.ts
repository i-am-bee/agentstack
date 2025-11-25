/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { isNotNull } from './helpers';

export function createMarkdownCodeBlock({ language, snippet }: { language: string; snippet: string }) {
  return `\`\`\`${language}\n${snippet}\n\`\`\``;
}

export function toMarkdownImage(url: string) {
  return `\n\n![](${url})\n\n`;
}

export function toMarkdownCitation({ text, sources }: { text: string; sources: string[] }) {
  return `[${text}](citation:${sources.join(',')})`;
}

export function createMarkdownSection({ heading, content }: { heading: string; content: string }) {
  return `
### ${heading}

${content}
`;
}

export function joinMarkdownSections(sections: (string | undefined)[]) {
  return sections.filter(isNotNull).join('\n\n');
}
