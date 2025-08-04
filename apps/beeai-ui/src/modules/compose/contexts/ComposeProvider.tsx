/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useSearchParams } from 'next/navigation';
import type { PropsWithChildren } from 'react';
import { useCallback, useEffect, useMemo, useRef } from 'react';
import { useFieldArray, useFormContext } from 'react-hook-form';
import { match } from 'ts-pattern';
import { v4 as uuid } from 'uuid';

import { buildA2AClient } from '#api/a2a/client.ts';
import type { ChatRun } from '#api/a2a/types.ts';
import { getErrorCode } from '#api/utils.ts';
import { useHandleError } from '#hooks/useHandleError.ts';
import { usePrevious } from '#hooks/usePrevious.ts';
import { useUpdateSearchParams } from '#hooks/useUpdateSearchParams.ts';
import { useAgent } from '#modules/agents/api/queries/useAgent.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { Role } from '#modules/messages/api/types.ts';
import { UIMessagePartKind, type UIUserMessage } from '#modules/messages/types.ts';
import { isNotNull } from '#utils/helpers.ts';

import type { UIComposePart } from '../a2a/types';
import { createSequentailInputDataPart, handleTaskStatusUpdate } from '../a2a/utils';
import { SEQUENTIAL_WORKFLOW_AGENT_NAME, SEQUENTIAL_WORKFLOW_AGENTS_URL_PARAM } from '../sequential/constants';
import type { ComposeStep, SequentialFormValues } from './compose-context';
import { ComposeContext, ComposeStatus } from './compose-context';

export function ComposeProvider({ children }: PropsWithChildren) {
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

  const { data: sequentialAgent } = useAgent({ name: SEQUENTIAL_WORKFLOW_AGENT_NAME });

  const a2aAgentClient = useMemo(
    () =>
      sequentialAgent &&
      buildA2AClient<UIComposePart>({
        providerId: sequentialAgent.provider.id,
        customStatusUpdateHandler: handleTaskStatusUpdate,
      }),
    [sequentialAgent],
  );

  const lastStep = steps.at(-1);
  const result = useMemo(() => lastStep?.result, [lastStep]);

  // const lastAgentIdx = 0;

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
            return agent ? { agent, instruction: '' } : null;
          })
          .filter(isNotNull),
      );
    }
  }, [agents, replaceSteps, searchParams, steps.length]);

  // const { isPending, stopAgent, reset } = useRunAgent({
  //   onDone: () => {
  //     const steps = getValues('steps');

  //     replaceSteps(
  //       steps.map((step) => {
  //         step.isPending = false;

  //         if (step.stats && !step.stats?.endTime) {
  //           step.stats.endTime = Date.now();
  //         }

  //         return step;
  //       }),
  //     );
  //   },
  //   onFailed: (_, error) => {
  //     handleError(error);
  //   },
  // TODO: A2A
  // onPart: (event) => {
  //   const { part } = event;
  //   if (isArtifactPart(part)) {
  //     return;
  //   }
  //   // TODO: we could probably figure out better typing
  //   const { agent_idx, content } = part as ComposeMessagePart;
  //   const step = getStep(agent_idx);
  //   if (!step) {
  //     return;
  //   }
  //   const updatedStep = {
  //     ...step,
  //     isPending: true,
  //     stats: {
  //       startTime: step.stats?.startTime ?? Date.now(),
  //     },
  //     result: `${step.result ?? ''}${content ?? ''}`,
  //   };
  //   updateStep(agent_idx, updatedStep);
  //   if (agent_idx > 0) {
  //     const stepsBefore = getValues('steps').slice(0, agent_idx);
  //     stepsBefore.forEach((step, stepsBeforeIndex) => {
  //       if (step.isPending || !step.stats?.endTime) {
  //         updateStep(stepsBeforeIndex, { ...step, isPending: false, stats: { ...step.stats, endTime: Date.now() } });
  //       }
  //     });
  //   }
  // },
  // onCompleted: (event) => {
  //   const finalAgentIdx = steps.length - 1;
  //   const output = extractOutput(
  //     event.run.output.map((message) => {
  //       return {
  //         ...message,
  //         parts: message.parts.filter((part) => (part as ComposeMessagePart).agent_idx === finalAgentIdx),
  //       };
  //     }),
  //   );
  //   const lastStep = getValues('steps').at(-1);
  //   updateStep(finalAgentIdx, { ...lastStep!, result: output });
  // },
  // onGeneric: (event) => {
  //   const { generic } = event;
  //   const { agent_idx } = generic;
  //   if (isNotNull(agent_idx)) {
  //     if (agent_idx !== lastAgentIdx) {
  //       const steps = getValues('steps');
  //       const pendingStepIndex = steps.findIndex((step) => step.isPending);
  //       const pendingStep = steps.at(pendingStepIndex);
  //       if (pendingStep) {
  //         const updatedStep = {
  //           ...pendingStep,
  //           isPending: false,
  //           stats: { ...pendingStep.stats, endTime: Date.now() },
  //         };
  //         updateStep(pendingStepIndex, updatedStep);
  //         const nextStepIndex = pendingStepIndex + 1;
  //         const nextStep = steps.at(pendingStepIndex + 1);
  //         if (nextStep) {
  //           const nextUpdatedStep = {
  //             ...nextStep,
  //             isPending: true,
  //             stats: {
  //               startTime: nextStep.stats?.startTime ?? Date.now(),
  //             },
  //           };
  //           updateStep(nextStepIndex, nextUpdatedStep);
  //         }
  //       }
  //     }
  //     if (generic) {
  //       const step = getStep(agent_idx);
  //       const metadata = createTrajectoryMetadata(generic);
  //       const updatedStep = {
  //         ...step,
  //         isPending: true,
  //         stats: {
  //           startTime: step.stats?.startTime ?? Date.now(),
  //         },
  //         logs: [...(step.logs ?? []), metadata?.message].filter(isNotNull),
  //       };
  //       updateStep(agent_idx, updatedStep);
  //     }
  //     lastAgentIdx = agent_idx;
  //   }
  // },
  // });

  // const getActiveStep = useCallback(() => getValues(`steps`).findLast(({ isPending }) => isPending), [getValues]);

  const updateStep = useCallback(
    (idx: number, value: ComposeStep) => {
      setValue(`steps.${idx}`, value);
    },
    [setValue],
  );

  const updateActiveStep = useCallback(
    (updater: (step: ComposeStep) => ComposeStep) => {
      const steps = getValues(`steps`);
      const activeStepIdx = steps.findLastIndex(({ isPending }) => isPending);
      if (activeStepIdx != -1) {
        const activeStep = steps.at(activeStepIdx);
        setValue(`steps.${activeStepIdx}`, updater(activeStep!));
      }
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
        step.isPending = false;

        if (step.stats && !step.stats?.endTime) {
          step.stats.endTime = Date.now();
        }

        return step;
      }),
    );
  }, [getValues, replaceSteps]);

  const send = useCallback(
    async (steps: ComposeStep[]) => {
      try {
        if (pendingRun.current || pendingSubscription.current) {
          throw new Error('A run is already in progress');
        }
        if (!a2aAgentClient) {
          throw new Error(`'${SEQUENTIAL_WORKFLOW_AGENT_NAME}' agent is not available.`);
        }

        steps.forEach((step, idx) => {
          updateStep(idx, {
            ...step,
            result: undefined,
            isPending: idx === 0,
            logs: [],
            stats:
              idx === 0
                ? {
                    startTime: Date.now(),
                  }
                : undefined,
          });
        });

        const userMessage: UIUserMessage = {
          id: uuid(),
          role: Role.User,
          parts: [createSequentailInputDataPart(steps)],
        };

        const run = a2aAgentClient.chat({
          message: userMessage,
          contextId: uuid(),
        });
        pendingRun.current = run;

        pendingSubscription.current = run.subscribe(({ parts }) => {
          parts.forEach((part) => {
            console.log({ part });

            match(part).with({ kind: UIMessagePartKind.Text }, (part) => {
              updateActiveStep((step) => {
                return {
                  ...step,
                  isPending: true,
                  stats: {
                    startTime: step.stats?.startTime ?? Date.now(),
                  },
                  result: `${step.result ?? ''}${part.text ?? ''}`,
                };
              });
            });
            // .with({ kind: UIComposePartKind.SequentialWorkflow }, (part) => {
            //   const activeStep = getActiveStep();
            // });
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
    [a2aAgentClient, updateStep, handleError, onDone],
  );

  const onSubmit = useCallback(() => {
    handleSubmit(async ({ steps }) => {
      await send(steps);
    })();
  }, [handleSubmit, send]);

  const handleCancel = useCallback(() => {
    const steps = getValues('steps');
    replaceSteps(
      steps.map((step) => ({
        ...step,
        stats: {
          ...step.stats,
          endTime: step.stats?.endTime ?? Date.now(),
        },
        isPending: false,
      })),
    );

    // stopAgent();
  }, [getValues, replaceSteps]);

  const handleReset = useCallback(() => {
    // reset();
    replaceSteps([]);
  }, [replaceSteps]);

  const isPending = useMemo(() => steps.some((step) => step.isPending), [steps]);

  const value = useMemo(
    () => ({
      result,
      status: isPending ? ComposeStatus.InProgress : result ? ComposeStatus.Completed : ComposeStatus.Ready,
      stepsFields,
      onSubmit,
      onCancel: handleCancel,
      onReset: handleReset,
    }),
    [result, isPending, stepsFields, onSubmit, handleCancel, handleReset],
  );

  return <ComposeContext.Provider value={value}>{children}</ComposeContext.Provider>;
}
