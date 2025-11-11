/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import 'katex/dist/katex.min.css';

import clsx from 'clsx';
import { useMemo } from 'react';
import Markdown from 'react-markdown';

import type { UISourcePart } from '#modules/messages/types.ts';

import { components, type ExtendedComponents } from './components';
import { CitationLink } from './components/CitationLink/CitationLink';
import { Code } from './components/Code';
import classes from './MarkdownContent.module.scss';
import { rehypePlugins } from './rehype';
import { remarkPlugins } from './remark';
import { urlTransform } from './utils';

interface Props {
  isPending?: boolean;
  sources?: UISourcePart[];
  children?: string;
  className?: string;
}

export function MarkdownContent({ isPending, sources, className, children }: Props) {
  const extendedComponents: ExtendedComponents = useMemo(
    () => ({
      ...components,
      citationLink: ({ ...props }) => <CitationLink {...props} sources={sources} />,
      code: ({ ...props }) => <Code {...props} forceExpand={isPending} />,
    }),
    [isPending, sources],
  );

  return (
    <div className={clsx(classes.root, className)}>
      <Markdown
        rehypePlugins={rehypePlugins}
        remarkPlugins={remarkPlugins}
        components={extendedComponents}
        urlTransform={urlTransform}
      >
        {children}
      </Markdown>
    </div>
  );
}
