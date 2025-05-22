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

import clsx from 'clsx';
import { memo } from 'react';

import type { Agent } from '../api/types';
import { getAgentDisplayName } from '../utils';
import classes from './AgentGreeting.module.scss';

interface Props {
  agent: Agent;
  className?: string;
  defaultGreeting?: string;
}

export const AgentGreeting = memo(function AgentGreeting({
  agent,
  className,
  defaultGreeting = DEFAULT_GREETING,
}: Props) {
  const userGreetingTemplate = agent.metadata.ui?.user_greeting ?? defaultGreeting;
  const userGreeting = renderVariables(userGreetingTemplate, {
    name: getAgentDisplayName(agent),
  });

  return <h1 className={clsx(classes.root, className)}>{userGreeting}</h1>;
});

function renderVariables(str: string, variables: Record<string, string>): string {
  return str.replace(/{(.*?)}/g, (_, key) => variables[key] ?? `{${key}}`);
}

const DEFAULT_GREETING = `Hi, I am {name}!
How can I help you?`;
