/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { ArrowRight } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import { ErrorPage } from '@i-am-bee/beeai-ui';

import { TransitionLink } from '@/components/TransitionLink/TransitionLink';
import { MainContent } from '@/layouts/MainContent';

export default function NotFoundPage() {
  return (
    <MainContent>
      <ErrorPage
        renderButton={({ className }) => (
          <Button as={TransitionLink} href="/" renderIcon={ArrowRight} className={className}>
            Buzz back to safety!
          </Button>
        )}
      />
    </MainContent>
  );
}
