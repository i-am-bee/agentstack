/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useSyncExternalStore } from 'react';

function subscribe(callback: (event: Event) => void) {
  window.addEventListener('online', callback);
  window.addEventListener('offline', callback);

  return () => {
    window.removeEventListener('online', callback);
    window.removeEventListener('offline', callback);
  };
}

export function useIsOnline() {
  const state = useSyncExternalStore(
    subscribe,
    () => window.navigator.onLine,
    () => true,
  );

  return state;
}
