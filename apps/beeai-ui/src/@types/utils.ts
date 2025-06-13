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

import type { paths } from '#api/schema.js';

export type ApiResponse<
  Path extends keyof paths,
  Method extends keyof paths[Path] & ('get' | 'post' | 'delete') = 'get',
  ContentType extends 'application/json' | 'text/event-stream' = 'application/json',
  StatusCode extends number = 200,
> = paths[Path][Method] extends {
  responses: {
    [code in StatusCode]: {
      content: {
        'application/json'?: infer JSON;
        'text/event-stream'?: infer EventStream;
      };
    };
  };
}
  ? ContentType extends 'application/json'
    ? JSON extends Record<string, unknown>
      ? JSON
      : never
    : EventStream extends Record<string, unknown>
      ? EventStream
      : never
  : never;

export type ApiRequest<
  Path extends keyof paths,
  Method extends keyof paths[Path] & ('get' | 'post' | 'delete' | 'put') = 'post',
  ContentType extends 'application/json' | 'multipart/form-data' = 'application/json',
> = paths[Path][Method] extends {
  requestBody?: {
    content: {
      'application/json'?: infer JSON;
      'multipart/form-data'?: infer FormData;
    };
  };
}
  ? ContentType extends 'application/json'
    ? JSON extends Record<string, unknown>
      ? JSON
      : never
    : FormData extends Record<string, unknown>
      ? FormData
      : never
  : never;

export type ApiQuery<
  Path extends keyof paths,
  Method extends keyof paths[Path] & 'get' = 'get',
> = paths[Path][Method] extends {
  parameters: { query?: infer Q };
}
  ? Q extends Record<string, unknown>
    ? Q
    : never
  : never;

export type ApiPath<
  Path extends keyof paths,
  Method extends keyof paths[Path] & ('get' | 'post' | 'put' | 'delete') = 'get',
> = paths[Path][Method] extends {
  parameters: { path?: infer P };
}
  ? P extends Record<string, unknown>
    ? P
    : never
  : never;
