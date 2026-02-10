/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type SubmitEvent, useState } from 'react';

import { useAgent } from './client';
import { BASE_URL, PROVIDER_ID } from './constants';
import type { ChatMessage } from './types';
import { createMessage } from './utils';

export function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);

  const { session, isInitializing, error, sendMessage } = useAgent();

  const isError = Boolean(error);
  const isSubmitDisabled = isInitializing || isSending || isError || !input.trim();

  const handleSubmit = async (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (isSubmitDisabled) {
      return;
    }

    const text = input.trim();

    setMessages((prevMessages) => [...prevMessages, createMessage({ role: 'user', text })]);
    setInput('');
    setIsSending(true);

    try {
      const response = await sendMessage({ text });

      setMessages((prevMessages) => [
        ...prevMessages,
        createMessage({ role: 'agent', text: response.text || 'No response from agent.' }),
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to send message';

      setMessages((prevMessages) => [...prevMessages, createMessage({ role: 'agent', text: `Error: ${message}` })]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <main className="app">
      <h1 className="heading">Agent Stack Chat Example</h1>

      <div className="meta">
        <p>
          <strong>Base URL:</strong> {BASE_URL}
        </p>

        <p>
          <strong>Provider ID:</strong> {PROVIDER_ID}
        </p>

        <p>
          <strong>Context ID:</strong> {session?.contextId}
        </p>
      </div>

      <div className="controls">
        <button className="button" type="button" onClick={() => window.location.reload()}>
          New session
        </button>
      </div>

      {messages.length > 0 && (
        <section className="messages">
          {messages.map((message) => (
            <article key={message.id} className={`message ${message.role}`}>
              <header>{message.role}</header>

              <p>{message.text}</p>
            </article>
          ))}
        </section>
      )}

      <div className="meta">
        <p>
          <strong>Status:</strong>{' '}
          {isError ? 'Error' : isInitializing ? 'Connecting to agent…' : isSending ? 'Agent is thinking…' : 'Ready'}
        </p>

        {isError && (
          <p className="error">
            <strong>Error:</strong> {error}
          </p>
        )}
      </div>

      <form className="form" onSubmit={handleSubmit}>
        <input
          className="input"
          type="text"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Type a message…"
          autoFocus
        />

        <button className="button" type="submit" disabled={isSubmitDisabled}>
          Send
        </button>
      </form>
    </main>
  );
}
