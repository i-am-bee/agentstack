/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import fs from 'fs';
import { join } from 'path';

import type { Post, PostModule } from './types';

const POSTS_DIR = join(process.cwd(), 'src/modules/blog/posts');

export async function getPostBySlug(slug: string): Promise<Post> {
  const {
    default: Content,
    metadata,
    readingTime: { text: readingTime },
  } = (await import(`@/modules/blog/posts/${slug}.mdx`)) as PostModule;

  if (!metadata.title || !metadata.date || !metadata.author) {
    throw new Error(`Missing some required metadata fields in: ${slug}`);
  }

  return {
    slug,
    metadata: {
      ...metadata,
      readingTime,
    },
    Content,
  };
}

export async function getAllPosts(): Promise<Post[]> {
  const slugs = fs.readdirSync(POSTS_DIR);
  const posts = (await Promise.all(slugs.map((slug) => getPostBySlug(slug.replace(/\.mdx$/, ''))))).sort((a, b) =>
    a.metadata.date > b.metadata.date ? -1 : 1,
  );

  return posts;
}
