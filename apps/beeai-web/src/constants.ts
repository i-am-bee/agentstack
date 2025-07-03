/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import packageJson from '../package.json';

export const RELEASE_VERSION = `v${packageJson.version}`;

export const DOCKER_MANIFEST_LABEL_NAME = 'beeai.dev.agent.yaml';

export const AGENT_REGISTRY_URL = `https://raw.githubusercontent.com/i-am-bee/beeai/refs/heads/v${RELEASE_VERSION}/agent-registry.yaml`;

export const SupportedDockerRegistries = ['ghcr.io'];
