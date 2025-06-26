/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { TRACEABILITY_LINK } from '#utils/constants.ts';

export function TracesTooltip() {
  return (
    <>
      <strong>Traceability Not Configured</strong>
      <br />
      <br />
      The traceability service isn't currently set up or reachable. To enable it, please check your configuration or
      follow the steps in our{' '}
      <a href={TRACEABILITY_LINK} target="_blank" rel="noreferrer">
        setup guide
      </a>
      .
    </>
  );
}
