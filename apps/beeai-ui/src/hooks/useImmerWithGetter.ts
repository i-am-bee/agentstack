/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Draft } from 'immer';
import { produce } from 'immer';
import { useMemo, useRef, useState } from 'react';

export type DraftFunction<S> = (draft: Draft<S>) => void;
export type Updater<S> = (arg: S | DraftFunction<S>) => void;

export function useImmerWithGetter<S>(initialValue: S): [S, () => S, Updater<S>] {
  const [value, setValue] = useState<S>(initialValue);
  const valueRef = useRef(value);

  return useMemo(
    () => [
      value,
      () => valueRef.current,
      (updater: S | DraftFunction<S>) => {
        valueRef.current =
          typeof updater === 'function' ? produce(updater as DraftFunction<S>, valueRef.current)() : updater;
        setValue(valueRef.current);
      },
    ],
    [setValue, value],
  );
}
