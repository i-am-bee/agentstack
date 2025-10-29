/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import type { ImgHTMLAttributes } from 'react';
import type { ExtraProps } from 'react-markdown';

import classes from './Img.module.scss';

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function Img({ node, className, ...props }: ImgHTMLAttributes<HTMLImageElement> & ExtraProps) {
  return (
    <span className={classes.root}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img {...props} className={clsx(classes.img, className)} alt={props.alt ?? ''} />
    </span>
  );
}
