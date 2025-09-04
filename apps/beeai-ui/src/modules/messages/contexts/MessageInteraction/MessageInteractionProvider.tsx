/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { type PropsWithChildren, useMemo, useState } from 'react';
import { useFocusWithin, useHover } from 'react-aria';

import { MessageInteractionContext, MessageInteractionPropsContext } from './context';

export function MessageInteractionProvider({ children }: PropsWithChildren) {
  const [isFocusWithin, setFocusWithin] = useState(false);

  const { isHovered, hoverProps } = useHover({});

  const { focusWithinProps } = useFocusWithin({ onFocusWithinChange: setFocusWithin });

  const propsValue = useMemo(
    () => ({
      props: {
        ...hoverProps,
        ...focusWithinProps,
      },
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- focusWithinProps causes unnecessary rerenders and it should be stable
    [hoverProps],
  );

  const value = useMemo(
    () => ({
      isHovered,
      isFocusWithin,
    }),
    [isHovered, isFocusWithin],
  );

  return (
    <MessageInteractionPropsContext.Provider value={propsValue}>
      <MessageInteractionContext.Provider value={value}>{children}</MessageInteractionContext.Provider>
    </MessageInteractionPropsContext.Provider>
  );
}
