import { CODE_ENTER } from 'keycode-js';
import { KeyboardEvent } from 'react';

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
