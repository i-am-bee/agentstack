/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useLocation, useNavigate } from 'react-router';

export function useViewTransition() {
  const location = useLocation();
  const navigate = useNavigate();

  const transitionTo = (path: string) => {
    if (!document.startViewTransition) {
      navigate(path); // Fallback for unsupported browsers
      return;
    }

    document.startViewTransition(() => navigate(path));
  };

  return { transitionTo, location };
}
