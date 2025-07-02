#!/usr/bin/env -S npx -y tsx@latest
/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */


import "./instrumentation.js";
import { AcpServer } from "@i-am-bee/acp-sdk/server/acp";

import { Version } from "beeai-framework";
import { runAgentProvider } from "@i-am-bee/beeai-sdk/providers/agent";
import { agent as contentJudge } from "./content-judge.js";

async function registerAgent(server: AcpServer) {
  server.agent(
    contentJudge.name,
    contentJudge.description,
    contentJudge.inputSchema,
    contentJudge.outputSchema,
    contentJudge.run,
    contentJudge.metadata
  );
}

export async function createServer() {
  const server = new AcpServer({
    name: "content-judge",
    version: Version,
  });
  await registerAgent(server);
  return server;
}

const server = await createServer();
await runAgentProvider(server);
