/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CODE_ENTER } from 'keycode-js';
import type { KeyboardEvent } from 'react';

export function submitFormOnEnter(event: KeyboardEvent<HTMLTextAreaElement>) {
  if (event.code === CODE_ENTER && !event.nativeEvent.isComposing && !event.shiftKey) {
    event.preventDefault();
    event.currentTarget.closest('form')?.requestSubmit();
  }
}

// Manually trigger the 'input' event to correctly resize TextAreaAutoHeight
export function dispatchInputEventOnFormTextarea(form: HTMLFormElement) {
  const elements = form.querySelectorAll('textarea');

  elements.forEach((element) => {
    const event = new Event('input', { bubbles: true });

    element.dispatchEvent(event);
  });
}
