/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// https://stackoverflow.com/a/19709846
const ABSOLUTE_URL_REGEX = new RegExp('^(?:[a-z+]+:)?//', 'i');

export const isAbsoluteUrl = (url: string) => ABSOLUTE_URL_REGEX.test(url);

export const isValidUrl = (value: string): boolean => {
  try {
    const url = new URL(value);
    return (url && url.protocol === 'http:') || url.protocol === 'https:';
  } catch {
    return false;
  }
};
