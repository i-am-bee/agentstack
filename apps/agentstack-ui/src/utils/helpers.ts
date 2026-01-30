/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import isMimeType from 'validator/lib/isMimeType';
import type { z, ZodObject } from 'zod';

import { ALL_FILES_CONTENT_TYPE, NO_FILES_CONTENT_TYPE } from '#modules/files/constants.ts';

export const noop = () => {};

/**
 * Predicate that tests if input value is not null.
 *
 * @example
 * const arr: (string | null)[] = ...;
 * const filtered = arr.filter(isNotNull); // filtered is correctly narrowed to string[]
 *
 * @param value nullable value
 * @returns true if value is not null of undefined
 */
export function isNotNull<T>(value: T | null | undefined): value is T {
  return value != null;
}

export function compareStrings(a: string, b: string): number {
  return a.localeCompare(b, 'en', { sensitivity: 'base' });
}

export function isValidContentType(type: string) {
  return (
    type === NO_FILES_CONTENT_TYPE ||
    type === ALL_FILES_CONTENT_TYPE ||
    type === 'audio/*' ||
    type === 'video/*' ||
    type === 'image/*' ||
    type === 'text/*' ||
    type === 'application/*' ||
    isMimeType(type)
  );
}

export function isImageMimeType(mimeType: string | undefined): boolean {
  return Boolean(mimeType?.toLowerCase().startsWith('image/'));
}

export function ensureBase64Uri(value: string, contentType?: string | null): string {
  const pattern = /^data:[^;]+;base64,/;

  if (pattern.test(value)) {
    return value;
  }

  return `data:${contentType};base64,${value}`;
}

export function getNameInitials(name: string | null | undefined) {
  if (!name) {
    return '';
  }

  // Names can have unicode characters in them, use unicode aware regex
  const matches = [...name.matchAll(/(\p{L}{1})\p{L}+/gu)];
  const initials = (matches.at(0)?.at(1) ?? '') + (matches.at(-1)?.at(1) ?? '');

  return initials.toUpperCase();
}

export function loadEnvConfig<T extends ZodObject>({
  schema,
  input,
  defaults = {},
}: {
  schema: T;
  input?: string;
  defaults?: Partial<z.input<T>>;
}): z.infer<T> {
  const safeDefaults = schema.partial().parse(defaults);

  if (!input) {
    return schema.parse(safeDefaults);
  }

  try {
    const parsed = JSON.parse(input);
    const result = schema.parse({
      ...safeDefaults,
      ...parsed,
    });

    return result;
  } catch (error) {
    console.error(error);

    return schema.parse(safeDefaults);
  }
}

export function findWithIndex<T>(
  array: T[],
  predicate: (value: T, index: number, obj: T[]) => boolean,
): [number, T] | [undefined, undefined] {
  const index = array.findIndex(predicate);
  if (index === -1) {
    return [undefined, undefined];
  }
  return [index, array[index]];
}
