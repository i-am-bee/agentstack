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

  const content = sources?.length
    ? `Lorem ipsum dolor, sit amet [consectetur](citation:${sources.at(0)?.key}) adipisicing elit. Nemo eveniet dicta
      architecto dolores minima, [recusandae placeat modi nam, itaque aspernatur](citation:${sources.at(2)?.key}) cumque culpa debitis quod facere
      corrupti eius quae praesentium [voluptates](citation:${sources.at(1)?.key},${sources.at(3)?.key}).`
    : children;

  return (
    <div className={clsx(classes.root, className)}>
      <Markdown remarkPlugins={remarkPlugins} components={extendedComponents}>
        {content}
      </Markdown>
    </div>
  );
}
