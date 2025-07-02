/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { AcpServer } from "@i-am-bee/acp-sdk/server/acp";
import { Metadata } from "@i-am-bee/beeai-sdk/schemas/metadata";
import {
  textInputSchema,
  textOutputSchema,
} from "@i-am-bee/beeai-sdk/schemas/text";
import {
  createRuntime,
  disposeRuntime,
  RuntimeOutputMethod,
} from "@i-am-bee/beekeeper";
import { CreateAgentConfig } from "@i-am-bee/beekeeper/agents/registry/registry.js";
import { Logger } from "beeai-framework";
import { z } from "zod";
import { AgentFactory } from "./agent-factory.js";
import { PlatformSdk } from "./platform-sdk.js";

const inputSchema = textInputSchema.extend({
  availableAgents: z.array(z.string()),
});
type Input = z.infer<typeof inputSchema>;
const outputSchema = textOutputSchema;

export const OUTPUT_DIR = `./beeai-supervisor-output`;
const run =
  (server: AcpServer) =>
  async (
    {
      params: { input, _meta },
    }: {
      params: {
        input: Input;
        _meta?: { progressToken?: string | number };
      };
    },
    { signal }: { signal?: AbortSignal }
  ) => {
    // ****************************************************************************************************
    // Connect platform
    // ****************************************************************************************************
    const platformSdk = PlatformSdk.getInstance();
    await platformSdk.init(
      input.availableAgents.map((a) => a.toLocaleLowerCase())
    );
    const listedPlatformAgents = await platformSdk.listAgents(signal);
    const agentConfigFixtures = listedPlatformAgents.map(
      ({ beeAiAgentId, description }) =>
        ({
          agentKind: "operator",
          agentConfigVersion: 1,
          agentType: beeAiAgentId,
          description: description,
          autoPopulatePool: false,
          instructions: "Not used",
          tools: [],
          maxPoolSize: 10,
        }) as CreateAgentConfig
    );

    let runtime;
    try {
      runtime = await createRuntime({
        agentConfigFixtures,
        agentFactory: new AgentFactory(),
        switches: {
          agentRegistry: {
            mutableAgentConfigs: false,
            restoration: false,
          },
          taskManager: {
            restoration: false,
          },
        },
        workspace: "beeai",
        outputDirPath: OUTPUT_DIR,
        logger: Logger.root,
        signal,
      });

      const output: RuntimeOutputMethod = async (output) => {
        let role;
        if (output.agent) {
          role = `🤖 [${output.agent.agentId}] `;
        } else {
          role = `📋 [${output.taskRun.taskRunId}] `;
        }

        if (_meta?.progressToken) {
          await server.server.sendAgentRunProgress({
            progressToken: _meta.progressToken,
            delta: {
              text: `${role} ${output.text}\n\n`,
            },
          });
        }
      };

      const response = await runtime.run(
        input.text,
        output,
        signal ?? new AbortController().signal
      ); // FIXME
      return {
        text: response || "",
        logs: [],
      };
    } finally {
      if (runtime) {
        disposeRuntime(runtime);
      }
    }
  };

const agentName = "beeai-supervisor";

export const agent = {
  name: agentName,
  description:
    "The agent autonomously breaks down tasks, assigns them to suitable agents, manages execution, evaluates outcomes, adapts workflows dynamically, and iterates until achieving an optimal solution.",
  inputSchema,
  outputSchema,
  run,
  metadata: {
    fullDescription: `The agent is an AI-powered, supervisor-led, task-driven system with the **BeeAI platform** integrated into the agent registry. The ${agentName} is a ReAct agent built with the **BeeAI framework**, which uses the *Task Manager* and *Agent Registry* tools to autonomously solve complex tasks.

## How It Works

1. When the agent receives an input message, it launches the supervisor runtime and initiates a predefined task called \`process_input_and_plan\`.
2. This task is associated with the supervisor agent, which begins processing the task input.
3. Based on the input, the supervisor checks the available agents and orchestrates the hierarchy of tasks to be performed.
4. Once the hierarchy of tasks completes, the final response is presented to the user as the output.
    
## Input Parameters 
The agent accepts structured input consisting of:

- **text** (string) - The user input.
- **availableAgents** (array of strings) – Agents available in the **BeeAI platform**.

## Output
Free text, depending on the output of the agents used.

## Key Features
- **Dynamic Task Orchestration** - Automates scheduling, management, and execution of tasks using the BeeAI platform.
- **Adaptive Decision-Making** - Leverages the ReAct-based supervisor to assign tasks to the most suitable agents in real time.
- **Scalability** - Supports integration with multiple agents, facilitating complex and large-scale task execution.
- **Autonomous Execution** - Minimizes human intervention by running tasks end-to-end with the supervisor agent.

## Use Cases
- **Customer Support** - Responds to user queries, delegates tasks to specialized agents, and provides comprehensive assistance.
- **Data Processing Pipelines** - Automates data extraction, transformation, and loading across various BeeAI agents.
- **Research Assistance** - Aggregates and analyzes information from multiple agents to speed up research tasks.
- **Workflow Automation** - Executes routine operations without manual oversight, reducing the risk of errors and saving time.
`,
    framework: "BeeAI",
    license: "Apache 2.0",
    languages: ["TypeScript"],
    githubUrl:
      "https://github.com/i-am-bee/beeai/blob/main/agents/official/beeai-framework/src/supervisor",
    examples: {
      cli: [
        {
          command: `beeai agent run ${agentName} '{"text":"Prepare a marketing strategy to sell most selling mobile phones in 2024 in Europe on my eshop. Ensure the strategy is based on top of thorough research of the market.", "availableAgents":["gpt-researcher","marketing-strategy"]}'`,
          name: "Marketing strategy",
          description:
            "Creates a marketing strategy for top-selling European mobile phones through supervisor-orchestrated workflow in the BeeAI platform. The supervisor agent intelligently coordinates a multi-step process where the gpt-researcher agent first conducts comprehensive market research, then passes these insights to the marketing-strategy agent which transforms the raw data into a tailored, actionable marketing plan for your e-shop. This demonstrates the platform's dynamic task orchestration and adaptive decision-making capabilities, delivering an integrated solution without requiring manual intervention between steps.",
        },
      ],
    },
  } satisfies Metadata,
};
