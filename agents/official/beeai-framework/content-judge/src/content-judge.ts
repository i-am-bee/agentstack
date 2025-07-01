/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from "zod";
import { SystemMessage, UserMessage } from "beeai-framework/backend/message";
import { Metadata } from "@i-am-bee/beeai-sdk/schemas/metadata";
import {
  textInputSchema,
  textOutputSchema,
} from "@i-am-bee/beeai-sdk/schemas/text";
import { Client as ACPClient } from "@i-am-bee/acp-sdk/client/index";
import { SSEClientTransport } from "@i-am-bee/acp-sdk/client/sse";
import { MODEL, API_BASE, API_KEY } from "./config.js";
import { OpenAIChatModel } from "beeai-framework/adapters/openai/backend/chat";

const inputSchema = textInputSchema.extend({
  documents: z.array(z.string()).default([]).optional(),
  agents: z.array(z.string()).default([]).optional(),
});
type Input = z.output<typeof inputSchema>;
const outputSchema = textOutputSchema;
type Output = z.output<typeof outputSchema>;

const criteria = [
  "correctness",
  "depth_and_coverage",
  "clarity_and_structure",
  "relevance",
] as const;
type Criteria = (typeof criteria)[number];

const structuredGenerationSchema = z.object(
  Object.fromEntries(criteria.map((c) => [c, z.number().min(0).max(1)])) as {
    [key in Criteria]: z.ZodNumber;
  }
);

// Define weighting for each evaluation criterion (using weighted average),
// make sure the sum of the weights equals 1
type Weights = { [key in Criteria]: number };
const weights: Weights = {
  correctness: 0.5,
  depth_and_coverage: 0.1,
  clarity_and_structure: 0.1,
  relevance: 0.3,
};

const EVALUATION_PROMPT = `Evaluate the quality of the generated document based on multiple criteria using a continuous scale from 0 (lowest quality) to 1 (highest quality). For each criterion, provide a numerical score (0-1):
- correctness: Assess whether the information is factually accurate based on reliable, authoritative sources. Penalize factual errors, misinterpretations, or unverified claims. Prioritize primary sources and well-established research when cross-checking.
- depth_and_coverage: Evaluate whether the document provides a comprehensive and well-rounded discussion of the topic. Consider whether key aspects are addressed, nuances are explored, and supporting evidence is provided. Compare the breadth and depth of the information against expectations for the topic.
- clarity_and_structure: Assess how well the document is organized. Check for logical flow, appropriate use of headings, bullet points, summaries, and coherence. Consider whether the language is clear, precise, and accessible to the intended audience.
- relevance: Measure the alignment between the document and the given research prompt or problem. Determine if the content remains focused on relevant aspects, avoiding tangents, unnecessary details, or off-topic discussions.`;

const calculateScore = (result: Weights) =>
  // Multiply by 100 and round to avoid floating precision problem when comparing
  Math.round(
    criteria.reduce((sum, key) => sum + result[key] * weights[key] * 100, 0)
  );

const retrieveDocuments = async ({
  text,
  agents,
  signal,
}: {
  text: string;
  agents: string[];
  signal?: AbortSignal;
}) => {
  const client = new ACPClient({
    name: "example-client",
    version: "1.0.0",
  });
  // TODO: Make this env-configurable.
  const transport = new SSEClientTransport(
    new URL("/mcp/sse", "http://localhost:8333")
  );

  try {
    await client.connect(transport);
  } catch (error) {
    console.error("Error connecting to ACP server:", error);
    throw error;
  }

  try {
    const { agents: platformAgents } = await client.listAgents(undefined, {
      signal,
    });
    const platformAgentsName = platformAgents.map((agent) => agent.name);

    if (!agents.every((agent) => platformAgentsName.includes(agent))) {
      throw new Error("One or more agents not available in the platform");
    }

    const results = await Promise.all(
      agents.map((agent) =>
        client.runAgent(
          {
            name: agent,
            input: { text },
          },
          {
            timeout: 10 * 60 * 1000,
            signal,
          }
        )
      )
    );

    return results.map(
      (result) => (result.output.text as string) || "No document"
    );
  } finally {
    await client.close();
  }
};

const run = async (
  {
    params,
  }: {
    params: { input: Input };
  },
  { signal }: { signal?: AbortSignal }
): Promise<Output> => {
  const { text, documents, agents } = params.input;
  if (!documents?.length && !agents?.length)
    return outputSchema.parse({ text: "No documents or agents provided." });

  let finalDocuments = documents || [];
  if (agents?.length) {
    finalDocuments = [
      ...finalDocuments,
      ...(await retrieveDocuments({ text, agents, signal })),
    ];
  }

  const model = new OpenAIChatModel(
    MODEL,
    {},
    { baseURL: API_BASE, apiKey: API_KEY, compatibility: "compatible" }
  );

  const results = await Promise.all(
    finalDocuments.map((document) =>
      // TODO: add progress update
      model.createStructure({
        schema: structuredGenerationSchema,
        messages: [
          // REVIEW: this essentially adds second system message because of the internal implementation of `createStructure`
          new SystemMessage(EVALUATION_PROMPT),
          new UserMessage(`Research prompt: ${text}\n\n Document: ${document}`),
        ],
        abortSignal: signal,
      })
    )
  );

  const scores = results.map((result) => calculateScore(result.object));
  const highestValueIndex = scores.reduce(
    (maxIndex, score, index, arr) => (score > arr[maxIndex] ? index : maxIndex),
    0
  );

  return outputSchema.parse({ text: finalDocuments[highestValueIndex] });
};

const agentName = "content-judge";

const exampleInputAgents: Input = {
  text: "Generate a concise summary of the history of artificial intelligence.",
  agents: ["gpt-researcher", "ollama-deep-researcher"],
};

const exampleOutputAgents =
  "Artificial Intelligence has evolved from early symbolic reasoning systems in the 1950s to deep learning-powered applications today, transforming industries such as healthcare, finance, and autonomous systems.";

const exampleInputDocuments: Input = {
  text: "How does quantum computing impact cryptography?",
  documents: [
    "Quantum computing poses a significant threat to classical encryption methods due to its ability to solve complex mathematical problems exponentially faster...",
    "Current cryptographic standards, such as RSA, rely on integer factorization, which quantum algorithms like Shor\\'s algorithm can efficiently break...",
    "Quantum computing will not significantly impact modern cryptography for at least another 50 years...",
  ],
  agents: ["gpt-researcher", "ollama-deep-researcher"],
};

const exampleOutputDocuments = `{
  "text": "Quantum computing poses a significant threat to classical encryption methods due to its ability to solve complex mathematical problems exponentially faster..."
}`;

export const agent = {
  name: agentName,
  description:
    "Evaluates multiple documents and agent-generated content based on correctness, depth, clarity, and relevance, selecting the highest-scoring one. It ensures optimal document quality for research, content validation, and knowledge refinement.",
  inputSchema,
  outputSchema,
  run,
  metadata: {
    framework: "BeeAI",
    license: "Apache 2.0",
    languages: ["TypeScript"],
    githubUrl:
      "https://github.com/i-am-bee/beeai/blob/main/agents/official/beeai-framework/src/content-judge",
    ui: { type: "custom" },
    examples: {
      cli: [
        {
          command: `beeai run ${agentName} '${JSON.stringify(exampleInputAgents, null, 2)}'`,
          name: "AI Content Refinement",
          description:
            "Provide agent names that will generate the content to compare.",
          output: exampleOutputAgents,
          processingSteps: [
            "No pre-provided documents are available, so it queries agents for content",
            "Evaluates and scores the generated responses based on correctness, clarity, and relevance",
            "Returns the best summary based on the highest score",
          ],
        },
        {
          command: `beeai run ${agentName} '${JSON.stringify(exampleInputDocuments, null, 2)}'`,
          name: "Research Validation",
          description: "Provide existing documents to compare.",
          processingSteps: [
            "Queries the agents for additional insights on quantum computing and cryptography",
            "Evaluates all gathered documents using the four scoring criteria",
            "Assigns scores and selects the document that best aligns with the research prompt",
          ],
        },
      ],
    },
    avgRunTimeSeconds: 22,
    avgRunTokens: 1229,
    fullDescription: `The agent evaluates multiple documents and agent-generated content based on four key criteria - correctness, depth & coverage, clarity & structure, and relevance. It assigns a numerical score (0-1) to each document for each criterion, using a weighted average to determine the highest-scoring document. This ensures that the most accurate, comprehensive, well-structured, and relevant document is selected.

## How It Works

The agent accepts two types of input:
- **Pre-provided documents** – Static documents submitted by the user or other agents.
- **Agent-generated content** – Content dynamically retrieved from specified agents in the system.

The agent processes all provided text inputs and evaluates them based on the defined criteria. It then selects the document with the highest weighted score and returns it as the best choice.

## Input Parameters

The agent operates based on the following input parameters:
- **text** (string) – The research prompt or query guiding document selection.
- **documents** (array of strings, optional) – A list of pre-provided documents for evaluation.
- **agents** (array of strings, optional) – A list of agents to query for additional content.

If no documents are provided, the agent relies entirely on agent-generated content.

## Evaluation Criteria:

1. **Correctness (50%)** – Assesses factual accuracy, penalizing misinformation.
2. **Depth & Coverage (10%)** – Measures how well the document explores key aspects of the topic.
3. **Clarity & Structure (10%)** – Evaluates logical organization and readability.
4. **Relevance (30%)** – Determines how well the document aligns with the given research prompt.

The agent utilizes the Llama 3.1 8B model to perform structured evaluations and scoring.

## Use Cases
- **Research Validation** – Ensures high-quality, well-researched content by selecting the most reliable sources.
- **Content Refinement** – Helps refine AI-generated content by scoring and selecting the most coherent and accurate version.
- **Document Summarization Assessment** – Evaluates multiple AI-generated summaries and chooses the most comprehensive one.
- **Quality Assurance for AI Outputs** – Ensures AI responses in a pipeline meet accuracy and relevance requirements.
`,
  } satisfies Metadata,
};
