#!/usr/bin/env -S npx -y tsx@latest --inspect
/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import "./instrumentation.js";
import "dotenv/config";

process.env.OPENAI_API_KEY ??= process.env.LLM_API_KEY;
process.env.OPENAI_MODEL_SUPERVISOR ??= process.env.LLM_MODEL ?? "llama3.1";
process.env.OPENAI_MODEL_OPERATOR ??= process.env.LLM_MODEL ?? "llama3.1";
process.env.OPENAI_API_ENDPOINT ??=
  process.env.LLM_API_BASE ?? "http://localhost:11434/v1";

import { AcpServer } from "@i-am-bee/acp-sdk/server/acp";

import { Version } from "beeai-framework";
import { runAgentProvider } from "@i-am-bee/beeai-sdk/providers/agent";
import { agent as supervisor } from "./supervisor/supervisor.js";

async function registerAgents(server: AcpServer) {
  server.agent(
    supervisor.name,
    supervisor.description,
    supervisor.inputSchema,
    supervisor.outputSchema,
    supervisor.run(server),
    supervisor.metadata
  );
}

export async function createServer() {
  const server = new AcpServer({
    name: "beeai-supervisor",
    version: Version,
  });
  await registerAgents(server);
  return server;
}

const server = await createServer();
await runAgentProvider(server);
