/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import isValidMimeType from 'validator/lib/isMimeType';

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

export function isMimeType(mimeType: string) {
  return (
    mimeType === 'audio/*' ||
    mimeType === 'video/*' ||
    mimeType === 'image/*' ||
    mimeType === 'text/*' ||
    mimeType === 'application/*' ||
    isValidMimeType(mimeType)
  );
}

export function isImageMimeType(mimeType: string | undefined): boolean {
  return Boolean(mimeType?.toLowerCase().startsWith('image/'));
}

export function objectFromEntries<const T extends ReadonlyArray<readonly [PropertyKey, unknown]>>(
  entries: T,
): { [K in T[number] as K[0]]: K[1] } {
  return Object.fromEntries(entries) as { [K in T[number] as K[0]]: K[1] };
}

export function ensureBase64Uri(value: string, contentType?: string | null): string {
  const pattern = /^data:[^;]+;base64,/;

  if (pattern.test(value)) {
    return value;
  }

  return `data:${contentType};base64,${value}`;
}
