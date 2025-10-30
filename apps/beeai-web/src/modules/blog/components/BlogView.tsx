/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Container } from '@i-am-bee/agentstack-ui';

import { routeDefinitions } from '@/utils/router';

import { getAllPosts } from '../api';
import { BlogHero } from './BlogHero';
import { PostPreview } from './PostPreview';

export async function BlogView() {
  const posts = await getAllPosts();

  return (
    <Container size="lg">
      <BlogHero />

      {posts.map(({ slug, metadata: { title, date, author, readingTime } }) => (
        <PostPreview
          key={slug}
          href={`${routeDefinitions.blog}/${slug}`}
          heading={title}
          date={date}
          author={author}
          readingTime={readingTime}
        />
      ))}
    </Container>
  );
}
