---
name: agentstack-client-sdk-essentials
description: Basic implementation guidelines how to work with Agent Stack client SDK
---

Custom GUI integration with Agent Stack requires dependency on both [A2A](https://a2a-protocol.org/latest/specification) as well as [Agent Stack](https://agentstack.beeai.dev/llms.txt).

You need to install both:

```bash
pnpm add @a2a-js/sdk agentstack-sdk
```

## Get list of available agents

You need to know the agent UUID in advance. The easiest way to obtain it is via Agent Stack API client which is a wrapper around Agent Stack server API.

Agents are also called Providers.

```ts
import { buildApiClient } from 'agentstack-sdk';

const agentstack = buildApiClient({ baseUrl: 'http://localhost:8334' });

const providers = await agentstack.listProviders({
    query: {}
})

if (providers.ok) {
  providers.data.items.forEach(provider => {
    console.log(`The agent is named ${provider.agent_card.name} with id ${provider.id}`)
  })
}
```

## Create Context and Token

Before creating A2A client, you must create a context (session) in Agent Stack. The context ID is used to correlate all communication throughout the conversation. It is also used for A2A client to communicate with the agents.

```ts
import { buildApiClient } from 'agentstack-sdk';

const agentstack = buildApiClient({ baseUrl: 'http://localhost:8334' });

const agentId = '548cd604-ce87-4ca4-b988-68357ca4cc40'

const context = await agentstack.createContext(agentId);

const { token } = await agentstack.createContextToken({
    contextId: context.id,

    globalPermissions: { llm: ['*'], a2a_proxy: ['*'] },

    contextPermissions: {
        files: ['*'],
        vector_stores: ['*'],
        context_data: ['*'],
    },
});

const contextId = context.id;
```

The `contextId` from Agent Stack MUST be used in all A2A messages. Do not generate your own UUID.

## Create A2A Client

Agent Stack SDK extends [A2A - Agent to Agent](https://a2a-protocol.org/latest/specification) protocol.

You need to create the client with a caveat that we need to provide fetch implemneation that packs in context token as authorization header.

Agent Stack SDK exposes helper to build the fetch `createAuthenticatedFetch`

```ts
import {
    ClientFactory,
    ClientFactoryOptions,
    DefaultAgentCardResolver,
    JsonRpcTransportFactory,
} from '@a2a-js/sdk/client';
import { createAuthenticatedFetch } from "agentstack-sdk";

const agentstackUrl = 'http://localhost:8334'

const agentUrl = `${agentstackUrl}/api/v1/a2a/${agentId}/agent-card.json`;

const fetchImpl = createAuthenticatedFetch(token);

const factory = new ClientFactory(
    ClientFactoryOptions.createFrom(ClientFactoryOptions.default, {
        transports: [new JsonRpcTransportFactory({ fetchImpl })],
        cardResolver: new DefaultAgentCardResolver({ fetchImpl }),
    }),
);
const a2aClient = await factory.createFromUrl(agentUrl);
```

## Multi turn (chat) conversation with the agent

Using A2A client to achieve multi turn (Chat) conversation with agent is relatively simple.

```ts
import type {
  Message,
  TaskArtifactUpdateEvent,
  TaskStatusUpdateEvent,
} from '@a2a-js/sdk';

const conversationHistory: Message[] = []

const clientPrompt = 'This is the initial message from user'

const clientMessage: Message = {
    messageId: crypto.randomUUID(),
    role: 'user',
    parts: [{ kind: 'text', text: clientPrompt }],
    kind: 'message',
    contextId,
    metadata: {}
};

const messageStream = a2aClient.sendMessageStream({ message: clientMessage });

function isStatusUpdate(event: unknown): event is TaskStatusUpdateEvent {
  return (
    typeof event === 'object' &&
    event !== null &&
    'kind' in event &&
    (event as { kind: string }).kind === 'status-update'
  );
}

let agentReply = ''
for await (const event of messageStream) {
    if (isStatusUpdate(event) && event.status?.message?.parts) {
        for (const part of event.status.message.parts) {
            if (part.kind === 'text') {
                agentReply += part.text
            }
        }
    }
}

console.log(`Client prompted ${clientPrompt} and agent responded with ${agentReply})
```

## Agent Stack Extensions

Agent Stack extends A2A with extensions. They are advertised via Agent Card and supplied via Message metadata.

Agents declare demands via agent card extensions. Client fulfills demands using dependency injection:

1. Fetch agent card from `/.well-known/agent-card.json`
2. Figure out the demands in the Agent Card
3. Fulfill the demands in the client
4. Assemble and send the fulfillment via Message metadata.

### Example of how fulfill LLM extension

```ts
import {
  buildApiClient,
  handleAgentCard,
  buildLLMExtensionFulfillmentResolver,
  type Fulfillments,
} from 'agentstack-sdk';

const agentCard = await a2aClient.getAgentCard();

const { resolveMetadata, demands } = handleAgentCard(agentCard);

const fulfillments: Fulfillments = {

    getContextToken: () => token,

    llm: async (demand) => {
      return {
        llm_fulfillments: Object.entries(demand.llm_demands).reduce((memo, [demandKey]) => {
          return {
            ...memo,
            [demandKey]: {
              api_model: 'gpt5',
              api_base: 'http://openai-endpoint',
              api_key: 'API_KEY'
            }
          }

        }, {})
      }
    }
};

const metadata = await resolveMetadata(fulfillments);

const message: Message = {
    messageId: crypto.randomUUID(),
    role: 'user',
    parts: [{ kind: 'text', text: 'Message content' }],
    kind: 'message',
    contextId,

    metadata,
};

const stream = a2aClient.sendMessageStream({ message });

```

The Agent Stack provides LLM OpenAI compatible service that can be easily used and automatically resolved.

```ts
import { buildLLMExtensionFulfillmentResolver } from 'agentstack-sdk';

if (demands.llmDemands) {
    fulfillments.llm = buildLLMExtensionFulfillmentResolver(agentstack, token);
}
```
