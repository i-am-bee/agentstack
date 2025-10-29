/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import { MessageFormContext, type MessageFormContextValue } from './message-form-context';

export function MessageFormProvider({ children, ...props }: PropsWithChildren<MessageFormContextValue>) {
  return <MessageFormContext.Provider value={props}>{children}</MessageFormContext.Provider>;
}
