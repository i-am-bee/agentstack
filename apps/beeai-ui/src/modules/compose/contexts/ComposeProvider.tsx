/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import { useSearchParams } from 'next/navigation';
import type { PropsWithChildren } from 'react';
import { useCallback, useEffect, useMemo, useRef } from 'react';
import { useFieldArray, useFormContext } from 'react-hook-form';
import { match } from 'ts-pattern';
import { v4 as uuid } from 'uuid';

import type { AgentA2AClient, ChatRun } from '#api/a2a/types.ts';
import { agentExtensionGuard, getErrorCode } from '#api/utils.ts';
import { useHandleError } from '#hooks/useHandleError.ts';
import { usePrevious } from '#hooks/usePrevious.ts';
import { useUpdateSearchParams } from '#hooks/useUpdateSearchParams.ts';
import { useAgentByName } from '#modules/agents/api/queries/useAgentByName.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { Role } from '#modules/messages/api/types.ts';
import { UIMessagePartKind, UIMessageStatus, type UIUserMessage } from '#modules/messages/types.ts';
import { addTranformedMessagePart, getMessageRawContent } from '#modules/messages/utils.ts';
import { usePlatformContext } from '#modules/platform-context/contexts/index.ts';
import { useEnsurePlatformContext } from '#modules/platform-context/hooks/useEnsurePlatformContext.ts';
import { useBuildA2AClient } from '#modules/runs/api/queries/useBuildA2AClient.ts';
import { AgentDemandsProvider } from '#modules/runs/contexts/agent-demands/AgentDemandsProvider.tsx';
import { useAgentDemands } from '#modules/runs/contexts/agent-demands/index.ts';
import { isNotNull } from '#utils/helpers.ts';

import { type UIComposePart, UIComposePartKind } from '../a2a/types';
import { createSequentialInputDataPart, handleTaskStatusUpdate } from '../a2a/utils';
import { SEQUENTIAL_WORKFLOW_AGENT_NAME, SEQUENTIAL_WORKFLOW_AGENTS_URL_PARAM } from '../sequential/constants';
import type { ComposeStep, SequentialFormValues } from './compose-context';
import { ComposeContext, ComposeStatus } from './compose-context';

export function ComposeProvider({ children }: PropsWithChildren) {
  const { data: sequentialAgent } = useAgentByName({ name: SEQUENTIAL_WORKFLOW_AGENT_NAME });

  useEnsurePlatformContext(sequentialAgent);

  const { agentClient } = useBuildA2AClient({
    providerId: sequentialAgent?.provider.id,
    extensions: (sequentialAgent?.capabilities.extensions ?? []).filter(agentExtensionGuard),
    onStatusUpdate: handleTaskStatusUpdate,
  });

  return (
    <AgentDemandsProvider agentClient={agentClient}>
      <ComposeProviderWithContext agentClient={agentClient}>{children}</ComposeProviderWithContext>
    </AgentDemandsProvider>
  );
}

interface Props {
  agentClient?: AgentA2AClient<UIComposePart>;
}

function ComposeProviderWithContext({ agentClient, children }: PropsWithChildren<Props>) {
  const { getContextId } = usePlatformContext();
  const { getFullfilments } = useAgentDemands();
  const { data: agents } = useListAgents({ onlyUiSupported: true, sort: true });

  const searchParams = useSearchParams();
  const { updateSearchParams } = useUpdateSearchParams();

  const errorHandler = useHandleError();

  const pendingSubscription = useRef<() => void>(undefined);
  const pendingRun = useRef<ChatRun<UIComposePart>>(undefined);

  const { handleSubmit, getValues, setValue, watch } = useFormContext<SequentialFormValues>();
  const stepsFields = useFieldArray<SequentialFormValues>({ name: 'steps' });
  const { replace: replaceSteps } = stepsFields;
  const steps = watch('steps');

  const lastStep = steps.at(-1);
  const result = useMemo(() => (lastStep?.result ? getMessageRawContent(lastStep.result) : undefined), [lastStep]);

  const previousSteps = usePrevious(steps);

  useEffect(() => {
    if (!agents || steps.length === previousSteps.length) return;

    updateSearchParams({
      [SEQUENTIAL_WORKFLOW_AGENTS_URL_PARAM]: steps.map(({ agent }) => agent.name).join(','),
    });
  }, [agents, steps, previousSteps, updateSearchParams]);

  useEffect(() => {
    if (!agents) return;

    const agentNames = searchParams
      ?.get(SEQUENTIAL_WORKFLOW_AGENTS_URL_PARAM)
      ?.split(',')
      .filter((item) => item.length);
    if (agentNames?.length && !steps.length) {
      replaceSteps(
        agentNames
          .map((name) => {
            const agent = agents.find((agent) => name === agent.name);
            return agent ? { agent, instruction: '', status: ComposeStatus.Ready } : null;
          })
          .filter(isNotNull),
      );
    }
  }, [agents, replaceSteps, searchParams, steps.length]);

  const getActiveStepIdx = useCallback(() => {
    const steps = getValues(`steps`);
    return steps.findLastIndex(({ status }) => status === ComposeStatus.InProgress);
  }, [getValues]);

  const updateStep = useCallback(
    (idx: number, updater: ComposeStep | ((step: ComposeStep) => ComposeStep)) => {
      const step = getValues(`steps`).at(idx);
      if (!step) {
        throw new Error(`Unexpected step at index ${idx}.`);
      }

      setValue(`steps.${idx}`, typeof updater === 'function' ? updater(step) : updater);
    },
    [getValues, setValue],
  );

  const handleError = useCallback(
    (error: unknown) => {
      const errorCode = getErrorCode(error);

      errorHandler(error, {
        errorToast: { title: errorCode?.toString() ?? 'Failed to run agent.', includeErrorMessage: true },
      });
    },
    [errorHandler],
  );

  const onDone = useCallback(() => {
    const steps = getValues('steps');

    replaceSteps(
      steps.map((step) => {
        return {
          ...step,
          status: ComposeStatus.Completed,
          stats: { ...step.stats, endTime: step.stats?.endTime ?? Date.now() },
        };
      }),
    );
  }, [getValues, replaceSteps]);

  const send = useCallback(
    async (steps: ComposeStep[]) => {
      try {
        if (pendingRun.current || pendingSubscription.current) {
          throw new Error('A run is already in progress');
        }
        if (!agentClient) {
          throw new Error(`'${SEQUENTIAL_WORKFLOW_AGENT_NAME}' agent is not available.`);
        }

        const contextId = getContextId();

        steps.forEach((step, idx) => {
          updateStep(idx, {
            ...step,
            result: undefined,
            status: idx === 0 ? ComposeStatus.InProgress : ComposeStatus.Ready,
            stats:
              idx === 0
                ? {
                    startTime: Date.now(),
                  }
                : undefined,
          });
        });
        const fulfillments = await getFullfilments();

        const userMessage: UIUserMessage = {
          id: uuid(),
          role: Role.User,
          parts: [createSequentialInputDataPart(steps)],
        };

        const run = agentClient.chat({
          message: userMessage,
          contextId,
          fulfillments,
        });
        pendingRun.current = run;

        pendingSubscription.current = run.subscribe(({ parts }) => {
          parts.forEach((part) => {
            match(part)
              .with({ kind: UIComposePartKind.SequentialWorkflow }, ({ agentIdx }) => {
                const activeStepIdx = getActiveStepIdx();

                if (activeStepIdx !== agentIdx) {
                  updateStep(activeStepIdx, (step) => ({
                    ...step,
                    status: ComposeStatus.Completed,
                    stats: { ...step.stats, endTime: Date.now() },
                  }));

                  updateStep(agentIdx, (step) => ({
                    ...step,
                    status: ComposeStatus.InProgress,
                    stats: {
                      startTime: step.stats?.startTime ?? Date.now(),
                    },
                  }));
                }
              })
              .otherwise((part) => {
                const activeStepIdx = getActiveStepIdx();

                const step = getValues(`steps.${activeStepIdx}`);
                const result = step.result ?? {
                  id: uuid(),
                  role: Role.Agent,
                  parts: [],
                  status: UIMessageStatus.InProgress,
                };

                const updatedParts = addTranformedMessagePart(part, result);
                result.parts = updatedParts;

                updateStep(activeStepIdx, { ...step, result });
              });
          });
        });

        await run.done;
      } catch (error) {
        handleError(error);
      } finally {
        onDone();
        pendingRun.current = undefined;
        pendingSubscription.current = undefined;
      }
    },
    [agentClient, getContextId, getFullfilments, updateStep, getActiveStepIdx, getValues, handleError, onDone],
  );

  const onSubmit = useCallback(() => {
    handleSubmit(async ({ steps }) => {
      await send(steps);
    })();
  }, [handleSubmit, send]);

  const handleCancel = useCallback(async () => {
    if (pendingRun.current && pendingSubscription.current) {
      const steps = getValues('steps');

      const hasContent = steps.some(({ result }) =>
        Boolean(result?.parts.some((part) => part.kind !== UIMessagePartKind.Text)),
      );

      replaceSteps(
        steps.map(({ stats, result, ...step }) => ({
          ...step,
          ...(hasContent
            ? {
                result,
                stats: {
                  ...stats,
                  endTime: stats?.endTime ?? Date.now(),
                },
              }
            : {
                status: ComposeStatus.Ready,
              }),
        })),
      );

      pendingSubscription.current();
      await pendingRun.current.cancel();
    } else {
      throw new Error('No run in progress');
    }
  }, [getValues, replaceSteps]);

  const handleReset = useCallback(() => {
    replaceSteps([]);
  }, [replaceSteps]);

  const value = useMemo(() => {
    let status = ComposeStatus.Ready;
    if (steps.some(({ status }) => status === ComposeStatus.InProgress)) {
      status = ComposeStatus.InProgress;
    } else if (steps.length && steps.every(({ status }) => status === ComposeStatus.Completed)) {
      status = ComposeStatus.Completed;
    }

    return {
      result,
      status,
      stepsFields,
      onSubmit,
      onCancel: handleCancel,
      onReset: handleReset,
    };
  }, [steps, result, stepsFields, onSubmit, handleCancel, handleReset]);

  return <ComposeContext.Provider value={value}>{children}</ComposeContext.Provider>;
}
