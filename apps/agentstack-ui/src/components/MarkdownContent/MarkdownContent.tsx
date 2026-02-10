/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import 'katex/dist/katex.min.css';

import clsx from 'clsx';
import type { Components } from 'react-markdown';
import Markdown from 'react-markdown';
import type { PluggableList } from 'unified';

import { components, type ExtendedComponents } from './components';
import { Code } from './components/Code';
import { MermaidDiagram } from './components/MermaidDiagram';
import { MermaidProvider } from './contexts';
import classes from './MarkdownContent.module.scss';
import { rehypePlugins } from './rehype';
import { remarkPlugins } from './remark';
import { urlTransform } from './utils';

export interface MarkdownContentProps {
  codeBlocksExpanded?: boolean;
  isStreaming?: boolean;
  children?: string;
  className?: string;
  remarkPlugins?: PluggableList;
  rehypePlugins?: PluggableList;
  components?: Components;
}

export function MarkdownContent({
  codeBlocksExpanded,
  isStreaming,
  className,
  remarkPlugins: remarkPluginsProps,
  rehypePlugins: rehypePluginsProps,
  components: componentsProps,
  children,
}: MarkdownContentProps) {
  const extendedComponents: ExtendedComponents = {
    ...components,
    code: ({ ...props }) => <Code {...props} forceExpand={codeBlocksExpanded} />,
    mermaidDiagram: (props) => <MermaidDiagram {...props} isStreaming={isStreaming} />,
    ...componentsProps,
  };

  const extendedRemarkPlugins = [...remarkPlugins, ...(remarkPluginsProps ?? [])];
  const extendedRehypePlugins = [...rehypePlugins, ...(rehypePluginsProps ?? [])];

  return (
    <MermaidProvider>
      <div className={clsx(classes.root, className)}>
        <Markdown
          rehypePlugins={extendedRehypePlugins}
          remarkPlugins={extendedRemarkPlugins}
          components={extendedComponents}
          urlTransform={urlTransform}
        >
          {children}
        </Markdown>
      </div>
    </MermaidProvider>
  );
}
