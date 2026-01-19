/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

type RegisterableHighlighter = { registerLanguage(name: string, func: unknown): void };

export async function registerLanguagesAsync(highlighter: RegisterableHighlighter) {
  const [
    { default: bash },
    { default: shell },
    { default: json },
    { default: yaml },
    { default: javascript },
    { default: typescript },
    { default: python },
  ] = await Promise.all([
    import('react-syntax-highlighter/dist/esm/languages/hljs/bash'),
    import('react-syntax-highlighter/dist/esm/languages/hljs/shell'),
    import('react-syntax-highlighter/dist/esm/languages/hljs/json'),
    import('react-syntax-highlighter/dist/esm/languages/hljs/yaml'),
    import('react-syntax-highlighter/dist/esm/languages/hljs/javascript'),
    import('react-syntax-highlighter/dist/esm/languages/hljs/typescript'),
    import('react-syntax-highlighter/dist/esm/languages/hljs/python'),
  ]);

  highlighter.registerLanguage('bash', bash);
  highlighter.registerLanguage('shell', shell);
  highlighter.registerLanguage('json', json);
  highlighter.registerLanguage('yaml', yaml);
  highlighter.registerLanguage('javascript', javascript);
  highlighter.registerLanguage('typescript', typescript);
  highlighter.registerLanguage('python', python);
}
