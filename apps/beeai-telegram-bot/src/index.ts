/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { A2AClient } from "@a2a-js/sdk/client";
import { Bot, Context, session, SessionFlavor } from "grammy";
import { config } from "dotenv"
import { createContext, createContextToken } from "./utils";

config()

interface Session {
    contextId: string | null
    contextToken: { token: string, expires_at: string } | null
}

type BotContext = Context & SessionFlavor<Session>

const bot = new Bot<BotContext>(process.env.BOT_TOKEN ?? "foobar")
const client = await A2AClient.fromCardUrl(process.env.AGENT_CARD_URL ?? "http://invalid")

bot.use(session({ initial: () => {
    return {
        contextId: null,
        contextToken: null
    } as Session
}}))

bot.on("message", async (ctx) => {
    const contextId = ctx.session.contextId ?? (await createContext()).id
    ctx.session.contextId = contextId
    const contextToken = ctx.session.contextToken ?? await createContextToken(contextId)
    ctx.session.contextToken = contextToken
    for await (const event of client.sendMessageStream({ 
        message: { 
            kind: "message",
            role: "user",
            messageId: Math.random().toString(),
            parts: [{kind: "text", text: ctx.message.text ?? "Say something"}],
            contextId: contextId,
            metadata: {
                "https://a2a-extensions.beeai.dev/services/platform_api/v1": {
                    "auth_token": contextToken.token,
                    "expires_at": contextToken.expires_at
                },
                "https://a2a-extensions.beeai.dev/services/llm/v1": {
                    "llm_fulfillments": {
                        "default": {
                            "identifier": "llm_proxy",
                            "api_base": "{platform_url}/api/v1/openai/",
                            "api_key": contextToken.token,
                            "api_model": "dummy"
                        }
                    }
                }
            }
        },
    })) {
        switch (event.kind) {
            case "message":
                for (const part of event.parts) {
                    if(part.kind == "text") {
                        await ctx.reply(part.text)
                    }
                }
                break;
            case "status-update":
                if (event.status.message){ 
                    for (const part of event.status.message.parts) {
                        if(part.kind == "text") {
                            await ctx.reply(part.text)
                        }
                    }
                }
                break;
            case "artifact-update":
                for (const part of event.artifact.parts) {
                    if(part.kind == "text") {
                        await ctx.reply(part.text)
                    }
                }
            default:
                break;
        }
    }
})

bot.start()
