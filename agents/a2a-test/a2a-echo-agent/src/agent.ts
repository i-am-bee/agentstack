/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { AgentCard } from "@a2a-js/sdk";

// 1. Agent metadata
export const echoAgent: AgentCard = {
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
