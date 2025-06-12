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
import { useCallback, useEffect, useMemo, useState } from 'react';

import { getErrorCode } from '#api/utils.ts';
import { useHandleError } from '#hooks/useHandleError.ts';
import { usePrevious } from '#hooks/usePrevious.ts';
import type { Agent } from '#modules/agents/api/types.ts';
import { useRunAgent } from '#modules/runs/hooks/useRunAgent.ts';
import type { RunLog, RunStats } from '#modules/runs/types.ts';
import { createMessagePart, extractOutput, isArtifact } from '#modules/runs/utils.ts';

import { useFileUpload } from '../../files/contexts';
import { HandsOffContext } from './hands-off-context';

interface Props {
  agent: Agent;
}

export function HandsOffProvider({ agent, children }: PropsWithChildren<Props>) {
  const [output, setOutput] = useState<string>('');
  const [stats, setStats] = useState<RunStats>();
  const [logs, setLogs] = useState<RunLog[]>([]);

  const errorHandler = useHandleError();

  const { clearFiles } = useFileUpload();
  const { input, isPending, runAgent, reset } = useRunAgent({
    onBeforeRun: () => {
      handleClear();
      setStats({ startTime: Date.now() });
    },
    onMessagePart: (event) => {
      const { part } = event;

      if (isArtifact(part)) {
        return;
      }

      const { content } = part;

      setOutput((output) => (content ? output.concat(content) : output));
    },
    onRunCompleted: (event) => {
      const output = extractOutput(event.run.output);

      setOutput(output);
    },
    onGeneric: (event) => {
      const log = event.generic;

      setLogs((logs) => [...logs, log]);
    },
    onDone: () => {
      handleDone();
    },
    onRunFailed: (event) => {
      const { error } = event.run;

      handleError(error);

      if (error) {
        setLogs((logs) => [...logs, error]);
      }
    },
  });

  const handleDone = useCallback(() => {
    setStats((stats) => ({ ...stats, endTime: Date.now() }));
  }, []);

  const handleError = useCallback(
    (error: unknown) => {
      const errorCode = getErrorCode(error);

      errorHandler(error, {
        errorToast: { title: errorCode?.toString() ?? 'Failed to run agent.', includeErrorMessage: true },
      });
    },
    [errorHandler],
  );

  const handleClear = useCallback(() => {
    reset();
    setOutput('');
    setStats(undefined);
    setLogs([]);
    clearFiles();
  }, [reset, clearFiles]);

  const previousAgent = usePrevious(agent);
  useEffect(() => {
    if (agent !== previousAgent) {
      handleClear();
    }
  }, [handleClear, agent, previousAgent]);

  const run = useCallback(
    async (input: string) => {
      const messageParts = [createMessagePart({ content: input })];

      try {
        await runAgent({ agent, messageParts });
      } catch (error) {
        handleError(error);
      }
    },
    [agent, runAgent, handleError],
  );

  const contextValue = useMemo(
    () => ({
      agent,
      input,
      output,
      stats,
      logs,
      isPending,
      onSubmit: run,
      onClear: handleClear,
    }),
    [agent, input, output, stats, logs, isPending, run, handleClear],
  );

  return <HandsOffContext.Provider value={contextValue}>{children}</HandsOffContext.Provider>;
}
