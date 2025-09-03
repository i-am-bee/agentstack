/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { use } from 'react';

import { MessageInteractionContext, MessageInteractionPropsContext } from './context';

export function useMessageInteractionProps() {
  const context = use(MessageInteractionPropsContext);

  if (!context) {
    throw new Error('useMessageInteractionProps must be used within a MessageInteractionProvider');
  }

  return context;
}

export function useMessageInteraction() {
  const context = use(MessageInteractionContext);

  if (!context) {
    throw new Error('useMessageInteraction must be used within a MessageInteractionProvider');
  }

  return context;
}
