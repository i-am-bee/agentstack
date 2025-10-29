/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { createContext, type Dispatch, type SetStateAction } from 'react';

export interface MessageFormContextValue {
  showSubmission: boolean;
  setShowSubmission: Dispatch<SetStateAction<boolean>>;
}

export const MessageFormContext = createContext<MessageFormContextValue | null>(null);
