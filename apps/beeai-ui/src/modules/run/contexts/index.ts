import { use } from 'react';
import { ChatContext, ChatMessagesContext } from './chat-context';

export function useChat() {
  const context = use(ChatContext);

  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }

  return context;
}

export function useChatMessages() {
  const context = use(ChatMessagesContext);

  if (!context) {
    throw new Error('useChatMessages must be used within a ChatProvider');
  }

  return context;
}
