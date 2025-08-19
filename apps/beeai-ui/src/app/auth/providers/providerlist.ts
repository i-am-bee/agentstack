/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import IBM from '#app/auth/providers/ibm.ts';

export class ProviderList {
  providerMap = new Map();
  static providerNames: string[] = ['ibm', 'ibmid', 'w3id'];
  constructor() {
    function getProviderFromName(name: string) {
      switch (name.toLocaleLowerCase()) {
        case 'w3id':
          return IBM;
        case 'ibmid':
          return IBM;
        case 'ibm':
          return IBM;
        default:
          return IBM;
      }
    }
    for (const provName of ProviderList.providerNames) {
      this.providerMap.set(provName, getProviderFromName(provName));
    }
  }
  public getProviderByName(name: string) {
    return this.providerMap.get(name);
  }
}
