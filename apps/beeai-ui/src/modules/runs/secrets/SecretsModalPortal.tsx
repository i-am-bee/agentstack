import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

import { useAgentSecrets } from '../contexts/agent-secrets';
import { SecretsModal } from './SecretsModal';

export function SecretsModalPortal() {
  const { secrets } = useAgentSecrets();
  const [isOpen, setIsOpen] = useState(false);
  // TODO: Do we want save the state in localStorage to avoid showing it again on subsequent visits?
  const [wasVisited, setWasVisited] = useState(false);

  useEffect(() => {
    if (wasVisited) {
      return;
    }

    const unresolvedSecrets = secrets.filter((s) => !s.isReady);

    if (unresolvedSecrets.length > 0) {
      setWasVisited(true);
      setIsOpen(true);
    }
  }, [secrets, wasVisited]);

  if (!isOpen || typeof document === 'undefined') {
    return null;
  }

  return createPortal(<SecretsModal isOpen={isOpen} onRequestClose={() => setIsOpen(false)} />, document.body);
}
