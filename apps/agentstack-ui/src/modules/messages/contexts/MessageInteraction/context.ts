/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';
import { createContext } from 'react';
import type { FocusWithinResult, HoverResult } from 'react-aria';

interface MessageInteractionPropsContextValue {
  props: HoverResult['hoverProps'] & FocusWithinResult['focusWithinProps'];
}

export const MessageInteractionPropsContext = createContext<MessageInteractionPropsContextValue>(
  null as unknown as MessageInteractionPropsContextValue,
);

interface MessageInteractionContextValue {
  isHovered: boolean;
  isFocusWithin: boolean;
}

export const MessageInteractionContext = createContext<MessageInteractionContextValue>(
  null as unknown as MessageInteractionContextValue,
);
