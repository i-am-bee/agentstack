/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import bash from 'react-syntax-highlighter/dist/esm/languages/hljs/bash';
import javascript from 'react-syntax-highlighter/dist/esm/languages/hljs/javascript';
import json from 'react-syntax-highlighter/dist/esm/languages/hljs/json';
import python from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import shell from 'react-syntax-highlighter/dist/esm/languages/hljs/shell';
import typescript from 'react-syntax-highlighter/dist/esm/languages/hljs/typescript';
import yaml from 'react-syntax-highlighter/dist/esm/languages/hljs/yaml';

export function registerLanguages<Highlighter extends { registerLanguage(name: string, func: unknown): void }>(
  highlighter: Highlighter,
) {
  highlighter.registerLanguage('bash', bash);
  highlighter.registerLanguage('shell', shell);
  highlighter.registerLanguage('json', json);
  highlighter.registerLanguage('yaml', yaml);
  highlighter.registerLanguage('javascript', javascript);
  highlighter.registerLanguage('typescript', typescript);
  highlighter.registerLanguage('python', python);
}
