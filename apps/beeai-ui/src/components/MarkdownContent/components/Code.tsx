/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
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
