/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { useQueryClient } from '@tanstack/react-query';
import type { AgentSettings } from 'beeai-sdk';
import { useRouter } from 'next/navigation';
import type { PropsWithChildren } from 'react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { v4 as uuid } from 'uuid';

import { type AgentA2AClient, type ChatRun, RunResultType } from '#api/a2a/types.ts';
import { createTextPart } from '#api/a2a/utils.ts';
import { agentExtensionGuard, getErrorCode } from '#api/utils.ts';
import { useHandleError } from '#hooks/useHandleError.ts';
import type { Agent } from '#modules/agents/api/types.ts';
import { FileUploadProvider } from '#modules/files/contexts/FileUploadProvider.tsx';
import { useFileUpload } from '#modules/files/contexts/index.ts';
import { convertFilesToUIFileParts } from '#modules/files/utils.ts';
import { Role } from '#modules/messages/api/types.ts';
import { useMessages } from '#modules/messages/contexts/Messages/index.ts';
import { MessagesProvider } from '#modules/messages/contexts/Messages/MessagesProvider.tsx';
import type { UIAgentMessage, UIMessageForm, UIUserMessage } from '#modules/messages/types.ts';
import { UIMessagePartKind, UIMessageStatus } from '#modules/messages/types.ts';
import { addTranformedMessagePart, isAgentMessage } from '#modules/messages/utils.ts';
import { contextKeys } from '#modules/platform-context/api/keys.ts';
import { usePlatformContext } from '#modules/platform-context/contexts/index.ts';
import { useEnsurePlatformContext } from '#modules/platform-context/hooks/useEnsurePlatformContext.ts';
import { useBuildA2AClient } from '#modules/runs/api/queries/useBuildA2AClient.ts';
import { useStartOAuth } from '#modules/runs/hooks/useStartOAuth.ts';
import { getSettingsRenderDefaultValues } from '#modules/runs/settings/utils.ts';
import type { RunStats } from '#modules/runs/types.ts';
import { SourcesProvider } from '#modules/sources/contexts/SourcesProvider.tsx';
import { getMessagesSourcesMap } from '#modules/sources/utils.ts';
import type { TaskId } from '#modules/tasks/api/types.ts';
import { isNotNull } from '#utils/helpers.ts';
import { routes } from '#utils/router.ts';

import { useAgentDemands } from '../agent-demands';
import { AgentDemandsProvider } from '../agent-demands/AgentDemandsProvider';
import { AgentSecretsProvider } from '../agent-secrets/AgentSecretsProvider';
import type { AgentRequestSecrets } from '../agent-secrets/types';
import { AgentStatusProvider } from '../agent-status/AgentStatusProvider';
import { AgentRunContext, AgentRunStatus } from './agent-run-context';

interface Props {
  agent: Agent;
}

export function AgentRunProviders({ agent, children }: PropsWithChildren<Props>) {
  const { agentClient } = useBuildA2AClient({
    providerId: agent.provider.id,
    extensions: (agent.capabilities.extensions ?? []).filter(agentExtensionGuard),
  });

  useEnsurePlatformContext(agent);

  return (
    <AgentSecretsProvider agent={agent} agentClient={agentClient}>
      <AgentDemandsProvider agentClient={agentClient}>
        <FileUploadProvider allowedContentTypes={agent.defaultInputModes}>
          <MessagesProvider>
            <AgentRunProvider agent={agent} agentClient={agentClient}>
              {children}
            </AgentRunProvider>
          </MessagesProvider>
        </FileUploadProvider>
      </AgentDemandsProvider>
    </AgentSecretsProvider>
  );
}

interface AgentRunProviderProps extends Props {
  agentClient?: AgentA2AClient;
}

function AgentRunProvider({ agent, agentClient, children }: PropsWithChildren<AgentRunProviderProps>) {
  const queryClient = useQueryClient();
  const router = useRouter();
  const errorHandler = useHandleError();

  const { messages, getMessages, setMessages } = useMessages();

  const [input, setInput] = useState<string>();
  const [isPending, setIsPending] = useState(false);
  const [stats, setStats] = useState<RunStats>();
  const settings = useRef<AgentSettings | undefined>(undefined);
  const pendingSubscription = useRef<() => void>(undefined);
  const pendingRun = useRef<ChatRun>(undefined);

  const { contextId, getContextId, updateContextWithAgentMetadata } = usePlatformContext();
  const { getFullfilments } = useAgentDemands();
  const { files, clearFiles } = useFileUpload();

  useEffect(() => {
    const settingsDemands = agentClient?.settingsDemands;
    if (settingsDemands) {
      settings.current = getSettingsRenderDefaultValues(settingsDemands);
    }
  }, [agentClient?.settingsDemands]);

  const updateCurrentAgentMessage = useCallback(
    (updater: (message: UIAgentMessage) => void) => {
      setMessages((messages) => {
        const lastMessage = messages.at(0); // messages are in reverse order

        if (lastMessage && isAgentMessage(lastMessage)) {
          updater(lastMessage);
        } else {
          throw new Error('There is no last agent message.');
        }
      });
    },
    [setMessages],
  );

  const handleError = useCallback(
    (error: unknown) => {
      const errorCode = getErrorCode(error);

      errorHandler(error, {
        errorToast: { title: errorCode?.toString() ?? 'Failed to run agent.', includeErrorMessage: true },
      });

      if (error instanceof Error) {
        updateCurrentAgentMessage((message) => {
          message.error = error;
          message.status = UIMessageStatus.Failed;
        });
      }
    },
    [errorHandler, updateCurrentAgentMessage],
  );

  const cancel = useCallback(async () => {
    if (pendingRun.current && pendingSubscription.current) {
      updateCurrentAgentMessage((message) => {
        message.status = UIMessageStatus.Aborted;
      });

      pendingSubscription.current();
      await pendingRun.current.cancel();
    } else {
      throw new Error('No run in progress');
    }
  }, [updateCurrentAgentMessage]);

  const clear = useCallback(() => {
    setMessages([]);
    setStats(undefined);
    clearFiles();
    setIsPending(false);
    setInput(undefined);
    pendingRun.current = undefined;

    router.push(routes.agentRun({ providerId: agent.provider.id }));
  }, [setMessages, clearFiles, router, agent.provider.id]);

  const checkPendingRun = useCallback(() => {
    if (pendingRun.current || pendingSubscription.current) {
      throw new Error('A run is already in progress');
    }
  }, []);

  const cancelPendingTask = useCallback(() => {
    const lastMessage = getMessages().at(0); // messages are in reverse order
    if (
      lastMessage &&
      isAgentMessage(lastMessage) &&
      lastMessage.status === UIMessageStatus.InputRequired &&
      lastMessage.taskId
    ) {
      agentClient?.cancelTask(lastMessage.taskId).catch((error) => {
        errorHandler(error, {
          errorToast: { title: 'Failed to cancel previous task.', includeErrorMessage: true },
        });
      });
    }
  }, [agentClient, errorHandler, getMessages]);

  const run = useCallback(
    async (message: UIUserMessage, taskId?: TaskId) => {
      if (!agentClient) {
        throw new Error('Agent client is not initialized');
      }

      checkPendingRun();
      updateContextWithAgentMetadata(agent);
      setIsPending(true);
      setStats({ startTime: Date.now() });

      const contextId = getContextId();

      const fulfillments = await getFullfilments();

      const agentMessage: UIAgentMessage = {
        id: uuid(),
        role: Role.Agent,
        parts: [],
        status: UIMessageStatus.InProgress,
      };

      setMessages((messages) => {
        messages.unshift(agentMessage, message);
      });

      try {
        const run = agentClient.chat({
          message,
          contextId,
          fulfillments,
          taskId,
          settings: settings.current,
        });
        pendingRun.current = run;

        let isFirstIteration = true;
        pendingSubscription.current = run.subscribe(({ parts, taskId: responseTaskId }) => {
          if (isFirstIteration) {
            queryClient.invalidateQueries({ queryKey: contextKeys.lists() });
          }

          updateCurrentAgentMessage((message) => {
            message.taskId = responseTaskId;
          });

          parts.forEach((part) => {
            updateCurrentAgentMessage((message) => {
              const updatedParts = addTranformedMessagePart(part, message);
              message.parts = updatedParts;
            });
          });

          isFirstIteration = false;
        });

        const result = await run.done;
        if (result && result.type === RunResultType.FormRequired) {
          updateCurrentAgentMessage((message) => {
            message.status = UIMessageStatus.InputRequired;
            message.parts.push({ kind: UIMessagePartKind.Form, ...result.form });
          });
        } else if (result && result.type === RunResultType.OAuthRequired) {
          updateCurrentAgentMessage((message) => {
            message.status = UIMessageStatus.InputRequired;
            message.parts.push({ kind: UIMessagePartKind.OAuth, url: result.url, taskId: result.taskId });
          });
        } else if (result && result.type === RunResultType.SecretRequired) {
          updateCurrentAgentMessage((message) => {
            message.status = UIMessageStatus.InputRequired;
            message.parts.push({
              kind: UIMessagePartKind.SecretRequired,
              secret: result.secret,
              taskId: result.taskId,
            });
          });
        } else {
          updateCurrentAgentMessage((message) => {
            message.status = UIMessageStatus.Completed;
          });
        }
      } catch (error) {
        handleError(error);
      } finally {
        setIsPending(false);
        setStats((stats) => ({ ...stats, endTime: Date.now() }));
        pendingRun.current = undefined;
        pendingSubscription.current = undefined;

        queryClient.invalidateQueries({ queryKey: contextKeys.lists() });
        queryClient.invalidateQueries({ queryKey: contextKeys.history({ contextId }) });
      }
    },
    [
      queryClient,
      checkPendingRun,
      getContextId,
      getFullfilments,
      setMessages,
      agentClient,
      agent,
      updateContextWithAgentMetadata,
      updateCurrentAgentMessage,
      handleError,
    ],
  );

  const chat = useCallback(
    (input: string) => {
      checkPendingRun();
      cancelPendingTask();

      setInput(input);

      const message: UIUserMessage = {
        id: uuid(),
        role: Role.User,
        parts: [createTextPart(input), ...convertFilesToUIFileParts(files)].filter(isNotNull),
      };

      clearFiles();

      return run(message);
    },
    [cancelPendingTask, checkPendingRun, clearFiles, files, run],
  );

  const submitForm = useCallback(
    (form: UIMessageForm, taskId?: TaskId) => {
      checkPendingRun();

      const message: UIUserMessage = {
        id: uuid(),
        role: Role.User,
        parts: [],
        form,
      };

      return run(message, taskId);
    },
    [checkPendingRun, run],
  );

  const { startAuth } = useStartOAuth({
    onSuccess: async (taskId: TaskId, redirectUri: string) => {
      const userMessage: UIUserMessage = {
        id: uuid(),
        role: Role.User,
        parts: [],
        auth: redirectUri,
      };

      await run(userMessage, taskId);
    },
  });

  const submitSecrets = useCallback(
    (runtimeFullfilledDemands: AgentRequestSecrets, taskId: TaskId) => {
      checkPendingRun();

      const message: UIUserMessage = {
        id: uuid(),
        role: Role.User,
        parts: [],
        runtimeFullfilledDemands,
      };

      return run(message, taskId);
    },
    [checkPendingRun, run],
  );

  const sources = useMemo(() => getMessagesSourcesMap(messages), [messages]);

  const status = useMemo(() => {
    if (!contextId || !agentClient) {
      return AgentRunStatus.Initializing;
    }
    if (isPending) {
      return AgentRunStatus.Pending;
    }
    return AgentRunStatus.Ready;
  }, [agentClient, contextId, isPending]);

  const onUpdateSettings = useCallback((values: AgentSettings) => {
    settings.current = values;
  }, []);

  const contextValue = useMemo(() => {
    return {
      agent,
      agentClient,
      status,
      isInitializing: status === AgentRunStatus.Initializing,
      isReady: status === AgentRunStatus.Ready,
      isPending: status === AgentRunStatus.Pending,
      hasMessages: Boolean(getMessages().length),
      input,
      stats,
      settingsRender: agentClient?.settingsDemands ?? null,
      chat,
      submitForm,
      startAuth,
      submitSecrets,
      cancel,
      clear,
      onUpdateSettings,
      getSettings: () => settings.current,
    };
  }, [
    agent,
    agentClient,
    cancel,
    chat,
    clear,
    getMessages,
    input,
    onUpdateSettings,
    startAuth,
    stats,
    status,
    submitForm,
    submitSecrets,
  ]);

  return (
    <AgentStatusProvider agent={agent} isMonitorStatusEnabled={isPending}>
      <SourcesProvider sources={sources}>
        <AgentRunContext.Provider value={contextValue}>{children}</AgentRunContext.Provider>
      </SourcesProvider>
    </AgentStatusProvider>
  );
}
