/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ArrowRight } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import { clsx } from 'clsx';

import classes from './HeadlineWithLink.module.scss';

interface Props {
  title: string;
  description: string;
  inverse?: boolean;
  buttonProps?: {
    url: string;
    label?: string;
  };
}

export function HeadlineWithLink({ title, inverse, description, buttonProps }: Props) {
  return (
    <div className={clsx(classes.root, { [classes.inverse]: inverse })}>
      <h2>{title}</h2>
      <p>{description}</p>
      {buttonProps && (
        <Button renderIcon={ArrowRight} href={buttonProps.url} target="_blank" rel="noreferrer">
          {buttonProps?.label ?? 'Learn more'}
        </Button>
      )}
    </div>
  );
}
