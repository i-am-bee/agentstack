/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { ArrowRight } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import { ErrorPage, TransitionLink } from '@i-am-bee/agentstack-ui';

import { MainContentView } from '@/layouts/MainContentView';
import { routeDefinitions } from '@/utils/router';

export default function NotFoundPage() {
  return (
    <MainContentView>
      <ErrorPage
        renderButton={({ className }) => (
          <Button as={TransitionLink} href={routeDefinitions.home} renderIcon={ArrowRight} className={className}>
            Buzz back to safety!
          </Button>
        )}
      />
    </MainContentView>
  );
}
