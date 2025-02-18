#!/usr/bin/env npx -y tsx@latest

import { AcpServer } from "@i-am-bee/acp-sdk/server/acp.js";

import { StreamlitAgent } from "bee-agent-framework/agents/experimental/streamlit/agent";
import { OllamaChatLLM } from "bee-agent-framework/adapters/ollama/chat";
import { UnconstrainedMemory } from "bee-agent-framework/memory/unconstrainedMemory";
import { Version } from "bee-agent-framework";
import { runAgentProvider } from "@i-am-bee/beeai-sdk/providers/agent";
import {
  promptInputSchema,
  promptOutputSchema,
  PromptOutput,
} from "@i-am-bee/beeai-sdk/schemas/prompt";
import { Metadata } from "@i-am-bee/beeai-sdk/schemas/metadata";

async function registerAgents(server: AcpServer) {
  const streamlitMeta = new StreamlitAgent({
    llm: new OllamaChatLLM(),
    memory: new UnconstrainedMemory(),
  }).meta;
  server.agent(
    streamlitMeta.name,
    streamlitMeta.description,
    promptInputSchema,
    promptOutputSchema,
    async ({
      params: {
        input: { prompt },
        _meta,
      },
    }) => {
      const output = await new StreamlitAgent({
        llm: new OllamaChatLLM(),
        memory: new UnconstrainedMemory(),
      })
        .run({ prompt })
        .observe((emitter) => {
          emitter.on("newToken", async ({ delta }) => {
            if (_meta?.progressToken) {
              await server.server.sendAgentRunProgress({
                progressToken: _meta.progressToken,
                delta: { text: delta } as PromptOutput,
              });
            }
          });
        });
      return {
        text: output.result.raw,
      };
    },
    {
      title: "Streamlit Agent",
      framework: "BeeAI",
      licence: "Apache 2.0",
      fullDescription: `This is an example AI agent.
## Features
- Feature 1  
- Feature 2  
- Feature 3`,
      avgRunTimeSeconds: 10,
      avgRunTokens: 48,
      ui: "chat",
    } as const satisfies Metadata
  );
}

export async function createServer() {
  const server = new AcpServer(
    {
      name: "Bee Agent Framework",
      version: Version,
    },
    {
      capabilities: {
        agents: {},
      },
    }
  );
  await registerAgents(server);
  return server;
}

const server = await createServer();
await runAgentProvider(server);
