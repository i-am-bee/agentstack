/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { CallApi } from '../core/types';
import { ApiMethod } from '../core/types';
import { readSystemConfigurationResponseSchema, updateSystemConfigurationResponseSchema } from './schemas';
import type { UpdateSystemConfigurationRequest } from './types';

export function createConfigurationApi(callApi: CallApi) {
  const readSystemConfiguration = () =>
    callApi({
      method: ApiMethod.Get,
      path: '/api/v1/configurations/system',
      schema: readSystemConfigurationResponseSchema,
    });

  const updateSystemConfiguration = ({ ...body }: UpdateSystemConfigurationRequest) =>
    callApi({
      method: ApiMethod.Put,
      path: '/api/v1/configurations/system',
      schema: updateSystemConfigurationResponseSchema,
      body,
    });

  return {
    readSystemConfiguration,
    updateSystemConfiguration,
  };
}
