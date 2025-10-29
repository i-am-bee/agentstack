/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { IBMProvider } from './ibm';

export function getProviderConstructor(name: string) {
  switch (name.toLocaleLowerCase()) {
    case 'w3id':
    case 'ibmid':
    case 'ibm':
      return IBMProvider;
    default:
      throw new Error(`No provider found for name: ${name}`);
  }
}
