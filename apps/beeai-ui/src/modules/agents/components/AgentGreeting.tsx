/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { memo } from 'react';

import { type Agent, InteractionMode } from '../api/types';
import { AgentWelcomeMessage } from './AgentWelcomeMessage';

interface Props {
  agent: Agent;
  defaultGreeting?: string;
}

export const AgentGreeting = memo(function AgentGreeting({ agent }: Props) {
  const {
    name,
    ui: { user_greeting, interaction_mode },
  } = agent;
  const defaultGreeting = interaction_mode
    ? DEFAULT_GREETINGS[interaction_mode]
    : DEFAULT_GREETINGS[InteractionMode.MultiTurn];
  const userGreeting = renderVariables(user_greeting ?? defaultGreeting, { name });

  return <AgentWelcomeMessage>{userGreeting}</AgentWelcomeMessage>;
});

function renderVariables(str: string, variables: Record<string, string>): string {
  return str.replace(/{(.*?)}/g, (_, key) => variables[key] ?? `{${key}}`);
}

const DEFAULT_GREETINGS = {
  [InteractionMode.MultiTurn]: `Hi, I am {name}!
How can I help you?`,
  [InteractionMode.SingleTurn]: 'What is your task?',
};
