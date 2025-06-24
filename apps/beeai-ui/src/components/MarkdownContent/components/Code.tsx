/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import isString from 'lodash/isString';
import type { HTMLAttributes } from 'react';
import type { ExtraProps } from 'react-markdown';

import { CopySnippet } from '#components/CopySnippet/CopySnippet.tsx';
import { SyntaxHighlighter } from '#components/SyntaxHighlighter/SyntaxHighlighter.tsx';

export function Code({ className, children }: HTMLAttributes<HTMLElement> & ExtraProps) {
  const language = getLanguage(className);

  if (!language) {
    return <code className={className}>{children}</code>;
  }

  if (!isString(children)) {
    return null;
  }

  return (
    <CopySnippet>
      <SyntaxHighlighter language={language}>{children}</SyntaxHighlighter>
    </CopySnippet>
  );
}

function getLanguage(className?: string): string | undefined {
  return className ? /language-(\w+)/.exec(className)?.[1] : undefined;
}
