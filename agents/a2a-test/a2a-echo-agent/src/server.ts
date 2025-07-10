/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import express from "express";
import cors from "cors";
import { v4 as uuidv4 } from "uuid";
import {
  AgentExecutor,
  RequestContext,
  ExecutionEventBus,
  InMemoryTaskStore,
  DefaultRequestHandler,
  A2AExpressApp,
} from "@a2a-js/sdk/server";
import { AgentCard, Task } from "@a2a-js/sdk";

const echoAgent: AgentCard = {
  name: "Echo Agent",
  description: "Echoes back what you say",
  url: "http://localhost:3000/",
  provider: { organization: "ExampleOrg", url: "https://example.com" },
  version: "1.0.0",
  capabilities: {
    streaming: true,
    pushNotifications: false,
    stateTransitionHistory: false,
  },
  defaultInputModes: ["text/plain"],
  defaultOutputModes: ["text/plain"],
  skills: [
    {
      id: "echo",
      name: "Echo",
      description: "Echo skill",
      tags: ["echo"],
      examples: ["Hello"],
    },
  ],
  supportsAuthenticatedExtendedCard: false,
};

class EchoExecutor implements AgentExecutor {
  private cancelled = new Set<string>();

  async cancelTask(taskId: string) {
    this.cancelled.add(taskId);
  }

  async execute(
    ctx: RequestContext,
    eventBus: ExecutionEventBus
  ): Promise<void> {
    const { userMessage, task, taskId, contextId } = ctx;
    const text = userMessage.parts
      .map((part) => part.kind === "text" && part.text)
      .join("");

    // initial task event
    if (!task) {
      const initial: Task = {
        kind: "task",
        id: taskId,
        contextId,
        status: {
          state: "submitted",
          timestamp: new Date().toISOString(),
        },
        history: [userMessage],
        metadata: userMessage.metadata,
        artifacts: [],
      };
      eventBus.publish(initial);
    }

    // working message
    eventBus.publish({
      kind: "status-update",
      taskId,
      contextId,
      status: {
        state: "working",
        message: {
          kind: "message",
          role: "agent",
          messageId: uuidv4(),
          parts: [{ kind: "text", text: "Echoing..." }],
          taskId,
          contextId,
        },
        timestamp: new Date().toISOString(),
      },
      final: false,
    });

    // simulate delay
    await new Promise((res) => setTimeout(res, 500));
    if (this.cancelled.has(taskId)) {
      eventBus.publish({
        kind: "status-update",
        taskId,
        contextId,
        status: {
          state: "canceled",
          timestamp: new Date().toISOString(),
        },
        final: true,
      });
      return;
    }

    // final echo response
    eventBus.publish({
      kind: "status-update",
      taskId,
      contextId,
      status: {
        state: "completed",
        message: {
          kind: "message",
          role: "agent",
          messageId: uuidv4(),
          parts: [{ kind: "text", text }],
          taskId,
          contextId,
        },
        timestamp: new Date().toISOString(),
      },
      final: true,
    });
  }
}

const store = new InMemoryTaskStore();
const executor = new EchoExecutor();
const handler = new DefaultRequestHandler(echoAgent, store, executor);

const app = express();
app.use(cors());

new A2AExpressApp(handler).setupRoutes(app, "");

app.listen(3000, () =>
  console.log("A2A server running at http://localhost:3000/")
);
