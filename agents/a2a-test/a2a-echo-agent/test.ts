/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { A2AClient } from "@a2a-js/sdk/client";
import { v4 as uuidv4 } from "uuid";

const client = new A2AClient("http://localhost:8000");

async function sendEcho(text: string) {
  const stream = client.sendMessageStream({
    message: {
      messageId: uuidv4(),
      role: "user",
      parts: [{ kind: "text", text }],
      kind: "message",
    },
  });

  for await (const ev of stream) {
    if (ev.kind === "status-update" && ev.status.message) {
      console.log(
        "Agent said:",
        ev.status.message.parts
          .map((part) => part.kind === "text" && part.text)
          .join("")
      );
    }
  }
}

sendEcho("Hello, world!");
