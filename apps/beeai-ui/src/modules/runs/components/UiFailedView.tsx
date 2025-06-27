/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ErrorMessage } from '#components/ErrorMessage/ErrorMessage.tsx';
import { Container } from '#components/layouts/Container.tsx';
import { MainContent } from '#components/layouts/MainContent.tsx';

interface Props {
  message?: string;
  isRefetching?: boolean;
  onRetry?: () => void;
}

export function UiFailedView({ message, isRefetching, onRetry }: Props) {
  return (
    <MainContent>
      <Container size="sm">
        <ErrorMessage
          title="Failed to load the agent."
          subtitle={message}
          isRefetching={isRefetching}
          onRetry={onRetry}
        />
      </Container>
    </MainContent>
  );
}
