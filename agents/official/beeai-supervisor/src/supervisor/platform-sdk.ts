import { Client as MCPClient } from "@i-am-bee/acp-sdk/client/index";
import { SSEClientTransport } from "@i-am-bee/acp-sdk/client/sse";
import { AgentRunProgressNotificationSchema } from "@i-am-bee/acp-sdk/types";
import { Logger } from "beeai-framework";
import { z } from "zod";

export class PlatformSdk {
  private static instance: PlatformSdk;

  protected readonly logger: Logger;
  private _initialized = false;
  private _connected = false;
  private transport: SSEClientTransport;
  private client: MCPClient;
  private availableAgents?: string[];
  private sdkUrl = new URL(`${process.env.PLATFORM_URL || "http://localhost:8333"}/mcp/sse`);

  private constructor() {
    this.logger = Logger.root.child({ name: this.constructor.name });
    this.transport = new SSEClientTransport(this.sdkUrl);
    this.client = new MCPClient(
      {
        name: "supervisor-agent",
        version: "1.0.0",
      },
      {}
    );
  }

  get initialized() {
    return this._initialized;
  }

  get connected() {
    return this._connected;
  }

  static getInstance() {
    if (!this.instance) {
      this.instance = new PlatformSdk();
    }
    return this.instance;
  }

  async init(availableAgents?: string[], autoConnect = true) {
    this.availableAgents = availableAgents;
    this._initialized = true;
    if (autoConnect) {
      await this.connect();
    }
  }

  async connect() {
    this.logger.info(`Connecting to platform`);
    if (this._connected) {
      this.logger.info(`Already connected`);
      return;
    }

    if (!this._initialized) {
      throw new Error(`Platform SDK wasn't initialized yet`);
    }
    try {
      await this.client.connect(this.transport);
      this._connected = true;
    } catch (err) {
      throw new Error(`Can't connect to Platform SDK on ${this.sdkUrl}`);
    }
  }

  private validate() {
    if (!this._initialized) {
      throw new Error(`Platform SDK isn't initialized`);
    }

    if (!this.connected) {
      throw new Error(`BeeAI Platform isn't connected`);
    }
  }

  async listAgents(signal?: AbortSignal) {
    this.logger.debug(`Listing agents`);
    const agents = await this.client.listAgents({}, { signal });

    return agents.agents
      .filter(
        (agent) =>
          !this.availableAgents || this.availableAgents.includes(agent.name)
      )
      .map((agent) => ({
        beeAiAgentId: agent.name,
        description: agent.description,
      }));
  }

  async runAgent(
    beeAiAgentId: string,
    prompt: string,
    notificationHandler: (
      notification: z.infer<typeof AgentRunProgressNotificationSchema>
    ) => void | Promise<void>,
    signal?: AbortSignal
  ) {
    this.logger.info({ beeAiAgentId, prompt }, `Running agent`);
    this.validate();

    const agents = await this.listAgents(signal);
    if (
      !agents.map(({ beeAiAgentId }) => beeAiAgentId).includes(beeAiAgentId)
    ) {
      throw new Error(
        `Agent ${beeAiAgentId} is not registered in the platform`
      );
    }

    this.client.setNotificationHandler(
      AgentRunProgressNotificationSchema,
      notificationHandler
    );

    return this.client.runAgent(
      {
        name: beeAiAgentId,
        input: { text: prompt },
      },
      { signal, timeout: 10 * 60 * 1000 }
    );
  }
}
