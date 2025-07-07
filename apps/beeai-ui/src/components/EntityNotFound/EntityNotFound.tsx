/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ArrowRight } from '@carbon/icons-react';
import { Button } from '@carbon/react';

import { ErrorPage } from '#components/ErrorPage/ErrorPage.tsx';
import { MainContent } from '#components/layouts/MainContent.tsx';
import { TransitionLink } from '#components/TransitionLink/TransitionLink.tsx';
import { routes } from '#utils/router.ts';

interface Props {
  type: 'agent';
}

export default function EntityNotFound({ type }: Props) {
  return (
    <MainContent>
      <ErrorPage
        message={`We couldn’t find the ${type} you are looking for.`}
        renderButton={({ className }) => (
          <Button as={TransitionLink} href={routes.home()} renderIcon={ArrowRight} className={className}>
            Buzz back to safety!
          </Button>
        )}
      />
    </MainContent>
  );
}
