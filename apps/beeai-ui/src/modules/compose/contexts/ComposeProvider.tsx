/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useSearchParams } from 'next/navigation';
import type { PropsWithChildren } from 'react';
import { useCallback, useEffect, useMemo } from 'react';
import { useFieldArray, useFormContext } from 'react-hook-form';

import { getErrorCode } from '#api/utils.ts';
import { useHandleError } from '#hooks/useHandleError.ts';
import { usePrevious } from '#hooks/usePrevious.ts';
import { useUpdateSearchParams } from '#hooks/useUpdateSearchParams.ts';
import { useAgent } from '#modules/agents/api/queries/useAgent.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { useRunAgent } from '#modules/runs/hooks/useRunAgent.ts';
import { isNotNull } from '#utils/helpers.ts';

import { SEQUENTIAL_WORKFLOW_AGENT_NAME, SEQUENTIAL_WORKFLOW_AGENTS_URL_PARAM } from '../sequential/constants';
import type { ComposeStep, SequentialFormValues } from './compose-context';
import { ComposeContext, ComposeStatus } from './compose-context';

export function ComposeProvider({ children }: PropsWithChildren) {
  const { data: agents } = useListAgents({ onlyUiSupported: true, sort: true });

  const searchParams = useSearchParams();
  const { updateSearchParams } = useUpdateSearchParams();

  const errorHandler = useHandleError();

  const { handleSubmit, getValues, setValue, watch } = useFormContext<SequentialFormValues>();
  const stepsFields = useFieldArray<SequentialFormValues>({ name: 'steps' });
  const { replace: replaceSteps } = stepsFields;
  const steps = watch('steps');

  const { data: sequentialAgent } = useAgent({ name: SEQUENTIAL_WORKFLOW_AGENT_NAME });

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

  const { isPending, stopAgent, reset } = useRunAgent({
    agent: sequentialAgent!,
    onDone: () => {
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
    },
    onFailed: (_, error) => {
      handleError(error);
    },
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
  });

  // const getStep = useCallback((idx: number) => getValues(`steps.${idx}`), [getValues]);

  const updateStep = useCallback(
    (idx: number, value: ComposeStep) => {
      setValue(`steps.${idx}`, value);
    },
    [setValue],
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

  const send = useCallback(
    async (steps: ComposeStep[]) => {
      try {
        if (!sequentialAgent) {
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

        // TODO: A2A
        // await runAgent({
        //   agent: sequentialAgent,
        //   parts: [
        //     createMessagePart({
        //       content: JSON.stringify({
        //         steps: steps.map(({ agent, instruction }) => ({ agent: agent.name, instruction })),
        //       }),
        //       content_type: 'application/json',
        //     }),
        //   ],
        // });
      } catch (error) {
        handleError(error);
      }
    },
    [sequentialAgent, updateStep, handleError],
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

    stopAgent();
  }, [stopAgent, getValues, replaceSteps]);

  const handleReset = useCallback(() => {
    reset();
    replaceSteps([]);
  }, [replaceSteps, reset]);

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
