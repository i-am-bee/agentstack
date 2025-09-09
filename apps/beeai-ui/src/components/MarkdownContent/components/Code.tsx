/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import isString from 'lodash/isString';
import type { HTMLAttributes } from 'react';
import type { ExtraProps } from 'react-markdown';

import { CodeSnippet } from '#components/CodeSnippet/CodeSnippet.tsx';
import { CopySnippet } from '#components/CopySnippet/CopySnippet.tsx';
import { SyntaxHighlighter } from '#components/SyntaxHighlighter/SyntaxHighlighter.tsx';

import classes from './Code.module.scss';

interface Props extends HTMLAttributes<HTMLElement>, ExtraProps {
  variant?: 'blog';
  inline?: boolean;
  forceExpand?: boolean;
}

export function Code({ variant, inline, forceExpand, className, children }: Props) {
  const language = getLanguage(className);

  if (!isString(children)) {
    return null;
  }

  if (language) {
    return (
      <CopySnippet variant={variant}>
        <SyntaxHighlighter language={language} variant={variant}>
          {children}
        </SyntaxHighlighter>
      </CopySnippet>
    );
  }

  if (inline) {
    return <code className={clsx(classes.inline, className)}>{children}</code>;
  }

  return (
    <CodeSnippet forceExpand={forceExpand} canCopy={!forceExpand}>
      {children}
    </CodeSnippet>
  );
}

function getLanguage(className?: string): string | undefined {
  return className ? /language-(\w+)/.exec(className)?.[1] : undefined;
}
