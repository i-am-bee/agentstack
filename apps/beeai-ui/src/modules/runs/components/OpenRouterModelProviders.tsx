/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { oauthMessageSchema } from '#api/a2a/extensions/services/oauth-provider.ts';
import { usePlatformContext } from '#modules/platform-context/contexts/index.ts';
import { Select } from '@carbon/react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useState } from 'react';

async function createSHA256CodeChallenge(input: string) {
  const encoder = new TextEncoder();
  const data = encoder.encode(input);
  const hash = await crypto.subtle.digest('SHA-256', data);
  return btoa(String.fromCharCode(...new Uint8Array(hash)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

// TODO: randomize
const codeVerifier = 'FoobarRandom12345';

export function OpenRouterModelProviders() {
  const { selectOpenRouterModel } = usePlatformContext();

  const [apiKey, setApiKey] = useState<string | null>(null);
  const [codeChallenge, setCodeChallenge] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);

  const models = useQuery({
    queryKey: ['openrouter-models'],
    queryFn: async () => {
      const data = await fetch('https://openrouter.ai/api/v1/models', {
        headers: {
          Authorization: `Bearer ${apiKey}`,
        },
      });
      return data.json();
    },
    enabled: Boolean(apiKey),
  });

  useEffect(() => {
    createSHA256CodeChallenge(codeVerifier).then(setCodeChallenge);
  }, []);

  const openAuthPopup = useCallback(() => {
    const url = `https://openrouter.ai/auth?callback_url=http://localhost:3000/oauth-callback&code_challenge=${codeChallenge}&code_challenge_method=S256`;

    const popup = window.open(url);
    if (!popup) {
      throw new Error('Failed to open popup');
    }
    popup.focus();

    // Check the status of opened window nad remove message listener, when it was closed
    const timer = setInterval(() => {
      if (popup.closed) {
        clearInterval(timer);
        window.removeEventListener('message', handler);
      }
    }, 500);

    async function handler(message: unknown) {
      const { success, data: parsedMessage } = oauthMessageSchema.safeParse(message);

      if (!success) {
        return;
      }

      if (popup) {
        window.removeEventListener('message', handler);
        popup.close();

        console.log(parsedMessage);
        const code = parsedMessage.data.redirect_uri.split('code=')[1];
        const response = await fetch('https://openrouter.ai/api/v1/auth/keys', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            code,
            code_verifier: codeVerifier,
            code_challenge_method: 'S256',
          }),
        });

        const data = await response.json();

        setApiKey(data.key);
      }
    }

    window.addEventListener('message', handler);
  }, [codeChallenge]);

  if (!apiKey) {
    return (
      <button type="button" onClick={openAuthPopup}>
        Get Model from OpenRouter
      </button>
    );
  }

  if (models.isLoading || !models.data) {
    return <div>Loading...</div>;
  }

  return (
    <select
      onChange={(e) => {
        setSelectedModel(e.target.value);

        selectOpenRouterModel(e.target.value, apiKey);
      }}
      value={selectedModel || ''}
    >
      {models.data.data
        .filter((model) => model.name.includes('free'))
        .map((model) => (
          <option value={model.id}>{model.name}</option>
        ))}
    </select>
  );
}
