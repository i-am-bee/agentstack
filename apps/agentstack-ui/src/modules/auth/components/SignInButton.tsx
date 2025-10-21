/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { Button } from '@carbon/react';

import Bee from '#svgs/bee.svg';

import type { AuthProvider } from '../types';

interface Props {
  provider: AuthProvider;
}

export function SignInButton({ provider }: Props) {
  return (
    <Button renderIcon={Bee} kind="secondary" type="submit">
      Log in with {provider.name}
    </Button>
  );
}
