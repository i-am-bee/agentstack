/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import type { PropsWithChildren } from 'react';
import { useCallback, useEffect, useMemo } from 'react';
import { useFieldArray, useFormContext } from 'react-hook-form';
import { useSearchParams } from 'react-router';

import { getErrorCode } from '#api/utils.ts';
import { useHandleError } from '#hooks/useHandleError.ts';
import { usePrevious } from '#hooks/usePrevious.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { useRunAgent } from '#modules/runs/hooks/useRunAgent.ts';
import { extractOutput, isArtifact } from '#modules/runs/utils.ts';
import { isNotNull } from '#utils/helpers.ts';

import { useSequentialAgent } from '../hooks/useSequentialAgent';
import { SEQUENTIAL_WORKFLOW_AGENT_NAME, SEQUENTIAL_WORKFLOW_AGENTS_URL_PARAM } from '../sequential/constants';
import type { ComposeMessagePart } from '../types';
import type { ComposeStep, SequentialFormValues } from './compose-context';
import { ComposeContext, ComposeStatus } from './compose-context';

export function ComposeProvider({ children }: PropsWithChildren) {
  const { data: availableAgents } = useListAgents();
  const [searchParams, setSearchParams] = useSearchParams();
  const errorHandler = useHandleError();

  const { handleSubmit, getValues, setValue, watch } = useFormContext<SequentialFormValues>();
  const stepsFields = useFieldArray<SequentialFormValues>({ name: 'steps' });
  const { replace: replaceSteps } = stepsFields;
  const steps = watch('steps');

  const sequentialAgent = useSequentialAgent();

  const previousSteps = usePrevious(steps);

  const lastStep = steps.at(-1);
  const result = useMemo(() => lastStep?.result, [lastStep]);

  let lastAgentIdx = 0;

  useEffect(() => {
    if (!availableAgents || steps.length === previousSteps.length) return;

    setSearchParams((searchParams) => {
      searchParams.set(SEQUENTIAL_WORKFLOW_AGENTS_URL_PARAM, steps.map(({ agent }) => agent.name).join(','));
      return searchParams;
    });
  }, [availableAgents, previousSteps.length, setSearchParams, steps]);

  useEffect(() => {
    if (!availableAgents) return;

    const agentNames = searchParams
      .get(SEQUENTIAL_WORKFLOW_AGENTS_URL_PARAM)
      ?.split(',')
      .filter((item) => item.length);
    if (agentNames?.length && !steps.length) {
      replaceSteps(
        agentNames
          .map((name) => {
            const agent = availableAgents.find((agent) => name === agent.name);
            return agent ? { agent, instruction: '' } : null;
          })
          .filter(isNotNull),
      );
    }
  }, [availableAgents, replaceSteps, searchParams, steps.length]);

  const { isPending, runAgent, stopAgent, reset } = useRunAgent({
    onMessagePart: (event) => {
      const { part } = event;

      if (isArtifact(part)) {
        return;
      }

      // TODO: we could probably figure out better typing
      const { agent_idx, content } = part as ComposeMessagePart;
      const step = getStep(agent_idx);

      if (!step) {
        return;
      }

      const updatedStep = {
        ...step,
        isPending: true,
        stats: {
          startTime: step.stats?.startTime ?? Date.now(),
        },
        result: `${step.result ?? ''}${content ?? ''}`,
      };

      updateStep(agent_idx, updatedStep);

      if (agent_idx > 0) {
        const stepsBefore = getValues('steps').slice(0, agent_idx);

        stepsBefore.forEach((step, stepsBeforeIndex) => {
          if (step.isPending || !step.stats?.endTime) {
            updateStep(stepsBeforeIndex, { ...step, isPending: false, stats: { ...step.stats, endTime: Date.now() } });
          }
        });
      }
    },
    onRunCompleted: (event) => {
      const finalAgentIdx = steps.length - 1;
      const output = extractOutput(
        event.run.output.map((message) => {
          return {
            ...message,
            parts: message.parts.filter((part) => (part as ComposeMessagePart).agent_idx === finalAgentIdx),
          };
        }),
      );
      const lastStep = getValues('steps').at(-1);

      updateStep(finalAgentIdx, { ...lastStep!, result: output });
    },
    onGeneric: (event) => {
      const { message, agent_idx } = event.generic;

      if (isNotNull(agent_idx)) {
        if (agent_idx !== lastAgentIdx) {
          const steps = getValues('steps');
          const pendingStepIndex = steps.findIndex((step) => step.isPending);
          const pendingStep = steps.at(pendingStepIndex);
          if (pendingStep) {
            const updatedStep = {
              ...pendingStep,
              isPending: false,
              stats: { ...pendingStep.stats, endTime: Date.now() },
            };
            updateStep(pendingStepIndex, updatedStep);

            const nextStepIndex = pendingStepIndex + 1;
            const nextStep = steps.at(pendingStepIndex + 1);
            if (nextStep) {
              const nextUpdatedStep = {
                ...nextStep,
                isPending: true,
                stats: {
                  startTime: nextStep.stats?.startTime ?? Date.now(),
                },
              };
              updateStep(nextStepIndex, nextUpdatedStep);
            }
          }
        }

        if (message) {
          const step = getStep(agent_idx);

          const updatedStep = {
            ...step,
            isPending: true,
            stats: {
              startTime: step.stats?.startTime ?? Date.now(),
            },
            logs: [...(step.logs ?? []), message],
          };

          updateStep(agent_idx, updatedStep);
        }

        lastAgentIdx = agent_idx;
      }
    },
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
    onRunFailed: (event) => {
      handleError(event.run.error);
    },
  });

  const getStep = useCallback((idx: number) => getValues(`steps.${idx}`), [getValues]);

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

        await runAgent({
          agent: sequentialAgent,
          content: JSON.stringify({
            steps: steps.map(({ agent, instruction }) => ({ agent: agent.name, instruction })),
          }),
          content_type: 'application/json',
        });
      } catch (error) {
        handleError(error);
      }
    },
    [sequentialAgent, runAgent, updateStep, handleError],
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
