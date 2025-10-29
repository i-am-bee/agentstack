/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Calendar, Pen, Time } from '@carbon/icons-react';
import type { IconProps } from '@carbon/icons-react/lib/Icon';
import type { ComponentType, PropsWithChildren } from 'react';

import { formatDate } from '../utils';
import classes from './PostMeta.module.scss';

interface Props {
  date: string;
  author: string;
  readingTime: string;
}

export function PostMeta({ date, author, readingTime }: Props) {
  return (
    <div className={classes.root}>
      <div className={classes.list}>
        <PostMetaItem icon={Calendar}>{formatDate(new Date(date))}</PostMetaItem>

        <PostMetaItem icon={Pen}>{author}</PostMetaItem>

        <PostMetaItem icon={Time}>{readingTime}</PostMetaItem>
      </div>
    </div>
  );
}

interface PostMetaItemProps extends PropsWithChildren {
  icon: ComponentType<IconProps>;
}

function PostMetaItem({ icon: Icon, children }: PostMetaItemProps) {
  return (
    <p className={classes.item}>
      <Icon className={classes.icon} />

      <span className={classes.label}>{children}</span>
    </p>
  );
}
