/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { A2AServiceExtension } from '../../../../core/extensions/types';
import { settingsDemandsSchema, settingsFulfillmentsSchema } from './schemas';
import type { SettingsDemands, SettingsFulfillments } from './types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/ui/settings/v1';

export const settingsExtension: A2AServiceExtension<typeof URI, SettingsDemands, SettingsFulfillments> = {
  getUri: () => URI,
  getDemandsSchema: () => settingsDemandsSchema,
  getFulfillmentsSchema: () => settingsFulfillmentsSchema,
};
