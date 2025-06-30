/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { isStringTerminalParameterSafe } from './strings';

function convertInputToCliArgument(input: string) {
  try {
    const parsed = JSON.parse(input);
    return `'${JSON.stringify(parsed, null, 2)}'`;
  } catch {
    return `"${input}"`;
  }
}

export default {
  beeai: {
    run(name: string, input?: string) {
      return [
        'beeai run',
        isStringTerminalParameterSafe(name) ? name : `'${name}'`,
        input ? convertInputToCliArgument(input) : '',
      ]
        .filter(Boolean)
        .join(' ');
    },
  },
};
