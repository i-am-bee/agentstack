/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ReactNode } from 'react';

import NotFound from '#svgs/NotFound.svg';

import { Container } from '../layouts/Container';
import classes from './ErrorPage.module.scss';

interface Props {
  message?: string;
  renderButton: (props: { className: string }) => ReactNode;
}

export function ErrorPage({ renderButton, message = 'We couldn’t find the page you are looking for.' }: Props) {
  return (
    <div className={classes.root}>
      <Container size="xs">
        <NotFound className={classes.image} />

        <h1 className={classes.heading}>Oooh, buzzkill.</h1>

        <p className={classes.description}>{message}</p>

        {renderButton({ className: classes.button })}
      </Container>
    </div>
  );
}
