/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ReactNode } from 'react';

import NotFound from '#svgs/NotFound.svg';

import { Container } from '../layouts/Container';
import classes from './ErrorPage.module.scss';

interface Props {
  renderButton: (props: { className: string }) => ReactNode;
}

export function ErrorPage({ renderButton }: Props) {
  return (
    <div className={classes.root}>
      <Container size="xs">
        <NotFound className={classes.image} />

        <h1 className={classes.heading}>Oooh, buzzkill.</h1>

        <p className={classes.description}>We couldn’t find the page you are looking for.</p>

        {renderButton({ className: classes.button })}
      </Container>
    </div>
  );
}
