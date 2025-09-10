/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { MDXContent } from 'mdx/types';
import type { ReadTimeResults } from 'reading-time';
import type { TocItem } from 'remark-flexible-toc';

export type PostToCItem = TocItem;

export interface Post {
  slug: string;
  metadata: PostMetadata;
  toc: PostToCItem[];
  Content: MDXContent;
}

export interface PostMetadata {
  title: string;
  date: string;
  author: string;
  readingTime: ReadTimeResults['text'];
}

export interface PostModule {
  default: MDXContent;
  metadata: Omit<PostMetadata, 'readTime'>;
  toc: TocItem[];
  readingTime: ReadTimeResults;
}
