/**
 * Copyright 2025 IBM Corp.
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
import Markdown from 'react-markdown';
import { PluggableList } from 'unified';
import classes from './MarkdownContent.module.scss';

interface Props {
  children?: string;
  className?: string;
}

export function MarkdownContent({ className, children }: Props) {
  return (
    <Markdown rehypePlugins={REHYPE_PLUGINS} className={clsx(classes.root, className)}>
      {children}
    </Markdown>
  );
}

const REHYPE_PLUGINS = [] satisfies PluggableList;
