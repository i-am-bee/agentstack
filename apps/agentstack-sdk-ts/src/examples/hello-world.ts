/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { TextPart } from '@a2a-js/sdk';

import { Server } from '../server';

const server = new Server();

server
  .agent({
    name: 'HelloWorld',
    description: 'A simple hello world agent',
    version: '0.0.1',
    detail: {
      interaction_mode: 'multi-turn',
      user_greeting: 'Hello! How can I help you?',
      author: { name: 'Agentstack' },
    },
    handler: async function* (input) {
      const firstPart = input.parts?.[0] as TextPart | undefined;
      if (firstPart?.kind === 'text') {
        yield `Hello! You said: ${firstPart.text}`;
      } else {
        yield `No text part found`;
      }
    },
  })
  .run({ port: 8000 });
