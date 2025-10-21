/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Container } from '#components/layouts/Container.tsx';

import { SignInHeading } from './SignInHeading';
import { SignInProviders } from './SignInProviders';
import classes from './SignInView.module.scss';

interface Props {
  callbackUrl?: string;
}

export function SignInView({ callbackUrl }: Props) {
  return (
    <div className={classes.root}>
      <Container size="full" className={classes.container}>
        <SignInHeading />

        <SignInProviders callbackUrl={callbackUrl} />
      </Container>
    </div>
  );
}
