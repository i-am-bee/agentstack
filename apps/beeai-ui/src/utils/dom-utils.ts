/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export function blurActiveElement() {
  const activeElem = document.activeElement;
  if (activeElem instanceof HTMLElement) {
    activeElem.blur();
  }
}
