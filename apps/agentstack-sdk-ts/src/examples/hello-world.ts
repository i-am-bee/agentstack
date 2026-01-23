/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { isTextPart } from '../experimental/server/a2a/utils';
import { InteractionMode } from '../extensions';
import { Server } from '../server';

const server = new Server();

server
  .agent({
    name: 'HelloWorld',
    description: 'A simple hello world agent',
    version: '0.0.1',
    detail: {
      interaction_mode: InteractionMode.MultiTurn,
      user_greeting: 'Hello! How can I help you?',
      author: {
        name: 'Agent Stack',
      },
    },
    handler: async function* (input) {
      const firstPart = input.parts.at(0);

      if (isTextPart(firstPart)) {
        yield `Hello! You said: ${firstPart.text}`;
      } else {
        yield `No text part found`;
      }
    },
  })
  .run({ port: 8000 });
