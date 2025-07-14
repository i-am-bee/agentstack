/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { memo } from 'react';

import { type Agent, UiType } from '../api/types';
import classes from './AgentGreeting.module.scss';

interface Props {
  agent: Agent;
  defaultGreeting?: string;
}

export const AgentGreeting = memo(function AgentGreeting({ agent }: Props) {
  const { display_name, user_greeting, ui_type } = agent.ui;
  const defaultGreeting = ui_type ? DEFAULT_GREETINGS[ui_type] : DEFAULT_GREETINGS[UiType.Chat];
  const userGreeting = renderVariables(user_greeting ?? defaultGreeting, { name: display_name });

  return <p className={clsx(classes.root, { [classes[`ui--${ui_type}`]]: ui_type })}>{userGreeting}</p>;
});

function renderVariables(str: string, variables: Record<string, string>): string {
  return str.replace(/{(.*?)}/g, (_, key) => variables[key] ?? `{${key}}`);
}

const DEFAULT_GREETINGS = {
  [UiType.Chat]: `Hi, I am {name}!
How can I help you?`,
  [UiType.HandsOff]: 'What is your task?',
};
