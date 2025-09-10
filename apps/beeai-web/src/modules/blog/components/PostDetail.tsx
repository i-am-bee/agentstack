/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Post } from '../types';
import classes from './PostDetail.module.scss';
import { PostMeta } from './PostMeta';
import { PostToC } from './PostToC';

interface Props {
  post: Post;
}

export function PostDetail({ post }: Props) {
  const {
    Content,
    metadata: { title, date, author, readingTime },
    toc,
  } = post;

  return (
    <article className={classes.root}>
      <header className={classes.header}>
        <h1 className={classes.heading}>{title}</h1>

        <PostMeta date={date} author={author} readingTime={readingTime} />
      </header>

      <div className={classes.body}>
        <div className={classes.toc}>
          <PostToC items={toc} />
        </div>

        <div className={classes.content}>
          <Content />
        </div>
      </div>
    </article>
  );
}
