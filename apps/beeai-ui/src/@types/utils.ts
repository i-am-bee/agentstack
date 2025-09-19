/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
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
  Method extends keyof paths[Path] & ('get' | 'post' | 'delete') = 'get',
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

export type RemoveIndexSignature<T> = {
  [K in keyof T as string extends K ? never : number extends K ? never : K]: T[K];
};

export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
