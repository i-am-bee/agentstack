/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';
import { useCallback, useContext, useEffect, useState } from 'react';
import React from 'react';

import { useCreateContext } from './api/mutations/useCreateContext';
import { useCreateContextToken } from './api/mutations/useCreateContextToken';

interface PlatformContext {
  contextId: string;
  resetContext: () => void;
  getPlatformToken: () => Promise<string>;
}

const PlatformContextWrapper = React.createContext<PlatformContext | null>(null);

export const useGetPlatformContext = () => {
  const context = useContext(PlatformContextWrapper);

  if (!context) {
    throw new Error('useGetContext must be used within a WithPlatformContext');
  }

  return context;
};

export function WithPlatformContext({ children }: PropsWithChildren) {
  const [contextId, setContextId] = useState<string | null>(null);
  const { mutateAsync: createContext } = useCreateContext();
  const { mutateAsync: createContextToken } = useCreateContextToken();

  const setContext = useCallback(
    (context: Awaited<ReturnType<typeof createContext>>) => {
      if (!context) {
        throw new Error(`Context has not been created`);
      }

      setContextId(context.id);
    },
    [setContextId],
  );

  const resetContext = useCallback(() => {
    setContextId(null);

    createContext().then(setContext);
  }, [createContext, setContext]);

  const getPlatformToken = useCallback(async () => {
    if (contextId === null) {
      throw new Error('Illegal State - Context ID is not set.');
    }

    const contextToken = await createContextToken({
      contextId,
      globalPermissionGrant: {
        llm: ['*'],
        a2a_proxy: [],
        contexts: [],
        embeddings: ['*'],
        feedback: [],
        files: [],
        providers: [],
        variables: [],
        vector_stores: [],
      },
      contextPermissionGrant: {
        files: ['*'],
        vector_stores: ['*'],
      },
    });

    if (!contextToken) {
      throw new Error('Could not generate context token');
    }

    return contextToken.token;
  }, [contextId]);

  useEffect(() => {
    createContext().then(setContext);
  }, [createContext, setContext]);

  if (contextId === null) {
    // TODO: visual?
    return null;
  }

  return (
    <PlatformContextWrapper.Provider value={{ contextId, resetContext, getPlatformToken }}>
      {children}
    </PlatformContextWrapper.Provider>
  );
}
