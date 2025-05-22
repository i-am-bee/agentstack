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

import { CODE_ENTER } from 'keycode-js';
import type { KeyboardEvent } from 'react';

export function submitFormOnEnter(event: KeyboardEvent<HTMLTextAreaElement>) {
  if (event.code === CODE_ENTER && !event.shiftKey) {
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
