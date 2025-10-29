/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Container } from '@i-am-bee/beeai-ui';
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

import { APP_NAME } from '@/constants';
import { MainContentView } from '@/layouts/MainContentView';
import { getAllPosts, getPostBySlug } from '@/modules/blog/api';
import { PostDetail } from '@/modules/blog/components/PostDetail';

interface Props {
  params: Promise<{ slug: string }>;
}

export default async function BlogPage({ params }: Props) {
  const { slug } = await params;
  const post = await getPostBySlug(slug);

  if (!post) {
    notFound();
  }

  return (
    <MainContentView>
      <Container size="lg">
        <PostDetail post={post} />
      </Container>
    </MainContentView>
  );
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const post = await getPostBySlug(slug);

  if (!post) {
    return notFound();
  }

  const title = `${post.metadata.title} | ${APP_NAME}`;

  return {
    title,
    openGraph: { title },
  };
}

export async function generateStaticParams() {
  const posts = await getAllPosts();

  return posts.map((post) => ({ slug: post.slug }));
}

export const dynamicParams = false;
