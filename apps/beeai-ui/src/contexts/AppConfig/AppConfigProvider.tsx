/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';
import { useMemo } from 'react';

import { useReadConfig } from './api/useReadConfig';
import { AppConfigContext } from './app-config-context';

export function AppConfigProvider({ children }: PropsWithChildren) {
  const { data } = useReadConfig();

  const contextValue = useMemo(() => ({ featureFlags: data }), [data]);

  return <AppConfigContext.Provider value={contextValue}>{children}</AppConfigContext.Provider>;
}
