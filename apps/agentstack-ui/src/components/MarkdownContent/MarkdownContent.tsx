/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import 'katex/dist/katex.min.css';

import clsx from 'clsx';
import { useMemo } from 'react';
import type { Components } from 'react-markdown';
import Markdown from 'react-markdown';
import type { PluggableList } from 'unified';

import { components, type ExtendedComponents } from './components';
import { Code } from './components/Code';
import classes from './MarkdownContent.module.scss';
import { rehypePlugins } from './rehype';
import { remarkPlugins } from './remark';
import { urlTransform } from './utils';

export interface MarkdownContentProps {
  codeBlocksExpanded?: boolean;
  children?: string;
  className?: string;
  remarkPlugins?: PluggableList;
  components?: Components;
}

export function MarkdownContent({
  codeBlocksExpanded,
  className,
  remarkPlugins: remarkPluginsProps,
  components: componentsProps,
  children,
}: MarkdownContentProps) {
  const extendedComponents: ExtendedComponents = useMemo(
    () => ({
      ...components,
      code: ({ ...props }) => <Code {...props} forceExpand={codeBlocksExpanded} />,
      ...componentsProps,
    }),
    [codeBlocksExpanded, componentsProps],
  );

  const extendedRemarkPlugins = useMemo(() => [...remarkPlugins, ...(remarkPluginsProps ?? [])], [remarkPluginsProps]);

  return (
    <div className={clsx(classes.root, className)}>
      <Markdown
        rehypePlugins={rehypePlugins}
        remarkPlugins={extendedRemarkPlugins}
        components={extendedComponents}
        urlTransform={urlTransform}
      >
        {children}
      </Markdown>
    </div>
  );
}
