/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import Link from 'next/link';

import { PostMeta } from './PostMeta';
import classes from './PostPreview.module.scss';

interface Props {
  href: string;
  heading: string;
  date: string;
  author: string;
  readingTime: string;
}

export function PostPreview({ href, heading, date, author, readingTime }: Props) {
  return (
    <article className={classes.root}>
      <h2 className={classes.heading}>
        <Link href={href} className={classes.link}>
          {heading}
        </Link>
      </h2>

      <PostMeta date={date} author={author} readingTime={readingTime} />
    </article>
  );
}
