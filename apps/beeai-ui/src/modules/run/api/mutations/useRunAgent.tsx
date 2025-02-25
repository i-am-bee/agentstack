/**
 * Copyright 2025 IBM Corp.
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

import { useMutation } from '@tanstack/react-query';
import { Agent } from '@i-am-bee/acp-sdk/types.js';
import z, { ZodLiteral, ZodObject } from 'zod';
import { useCreateMCPClient } from '#api/mcp-client/useCreateMCPClient.ts';

interface Props<
  NotificationsSchema extends ZodObject<{
    method: ZodLiteral<string>;
  }>,
> {
  agent: Agent;
  notifications?: {
    schema: NotificationsSchema;
    handler: (notification: z.infer<NotificationsSchema>) => void | Promise<void>;
  };
}

export function useRunAgent<
  Input extends { [x: string]: unknown },
  NotificationsSchema extends ZodObject<{
    method: ZodLiteral<string>;
  }>,
>({ agent, notifications }: Props<NotificationsSchema>) {
  const createClient = useCreateMCPClient();

  const { mutateAsync, isPending } = useMutation({
    mutationFn: async ({ input, abortController }: { input: Input; abortController?: AbortController }) => {
      const client = await createClient();
      if (!client) throw new Error('Connecting to MCP server failed.');

      if (notifications) {
        client.setNotificationHandler(notifications.schema, notifications.handler);
      }

      return client.runAgent(
        {
          _meta: { progressToken: notifications ? crypto.randomUUID() : undefined },
          name: agent.name,
          input,
        },
        {
          timeout: 10 * 60 * 1000, // 10 minutes
          signal: abortController?.signal,
        },
      );
    },
  });

  return { runAgent: mutateAsync, isPending };
}
