/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { useMemo } from 'react';
import Markdown from 'react-markdown';

import type { SourceReference } from '#modules/runs/sources/api/types.ts';

import { components, type ExtendedComponents } from './components';
import { InlineCitations } from './components/CitationLink/InlineCitations';
import classes from './MarkdownContent.module.scss';
import { remarkPlugins } from './remark';

interface Props {
  sources?: SourceReference[];
  children?: string;
  className?: string;
}

export function MarkdownContent({ sources, className, children }: Props) {
  const extendedComponents: ExtendedComponents = useMemo(
    () => ({
      ...components,
      citationLink: ({ keys, children }) => {
        const filteredSources = sources?.filter(({ key }) => keys.includes(key));

        return <InlineCitations sources={filteredSources}>{children}</InlineCitations>;
      },
    }),
    [sources],
  );

  return (
    <div className={clsx(classes.root, className)}>
      <Markdown remarkPlugins={remarkPlugins} components={extendedComponents}>
        {children}
      </Markdown>
    </div>
  );
}
