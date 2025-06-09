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

import { useListVariables } from '#modules/variables/api/queries/useListVariables.ts';
import { AGENT_DISPLAY_MODEL_TEMP } from '#utils/constants.ts';

import classes from './AgentModel.module.scss';

export function AgentModel() {
  const { data, isPending } = useListVariables({ errorToast: false, retry: false });

  // TEMP: Fetching the variables list will fail in production deployment,
  // so we check `isPending` and use a fallback once any response is received.
  // This is temporary solution until the agent model is returned by API.
  if (isPending) {
    return null;
  }

  const model = data?.env.LLM_MODEL ?? AGENT_DISPLAY_MODEL_TEMP;

  return <div className={classes.root}>{model}</div>;
}
