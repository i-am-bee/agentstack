/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';
import { useMemo } from 'react';

import { FeatureFlags } from '#utils/feature-flags.ts';

import { AppConfigContext } from './app-config-context';

interface Props {
  featureFlags: FeatureFlags;
}

export function AppConfigProvider({ featureFlags, children }: PropsWithChildren<Props>) {
  const contextValue = useMemo(() => ({ featureFlags }), [featureFlags]);

  return <AppConfigContext.Provider value={contextValue}>{children}</AppConfigContext.Provider>;
}
