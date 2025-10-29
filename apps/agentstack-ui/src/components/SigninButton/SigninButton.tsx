/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { Button } from '@carbon/react';

import Bee from '#svgs/bee.svg';

interface Props {
  provider: {
    id: string;
    name: string;
  };
}

export function SigninButton({ provider }: Props) {
  return (
    <Button renderIcon={Bee} iconDescription={`Signin with ${provider.name}`} kind="secondary" type="submit">
      <span>Login with {provider.name}</span>
    </Button>
  );
}
