/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

import { useAgentSecrets } from '../contexts/agent-secrets';
import { SecretsModal } from './SecretsModal';

export function SecretsModalPortal() {
  const { hasSeenModal, markModalAsSeen, demandedSecrets } = useAgentSecrets();
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (hasSeenModal) {
      return;
    }
    const unresolvedSecrets = demandedSecrets.filter((s) => !s.isReady);

    if (unresolvedSecrets.length > 0) {
      markModalAsSeen();
      setIsOpen(true);
    }
  }, [hasSeenModal, markModalAsSeen, demandedSecrets]);

  if (!isOpen || typeof document === 'undefined') {
    return null;
  }

  return createPortal(<SecretsModal isOpen={isOpen} onRequestClose={() => setIsOpen(false)} />, document.body);
}
