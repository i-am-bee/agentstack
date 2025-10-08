/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import packageJson from '../package.json';

export const DOCKER_MANIFEST_LABEL_NAME = 'beeai.dev.agent.json';

export const AGENT_REGISTRY_URL = `https://raw.githubusercontent.com/i-am-bee/beeai/refs/tags/v${packageJson.version}/agent-registry.yaml`;

export const SupportedDockerRegistries = ['ghcr.io'];

export const GITHUB_REPO_LINK = 'https://github.com/i-am-bee/beeai-framework';

export const FRAMEWORK_QUICKSTART_LINK = 'https://framework.beeai.dev/introduction/quickstart';

export const FRAMEWORK_DOCS_LINK = 'https://framework.beeai.dev';

export const FRAMEWORK_INTRO_LINK = 'https://framework.beeai.dev/introduction/welcome';

export const PLATFORM_INTRO_LINK = 'https://docs.beeai.dev/introduction/welcome';

export const DISCORD_LINK = 'https://discord.gg/NradeA6ZNF';

export const YOUTUBE_LINK = 'https://www.youtube.com/@BeeAIAgents';

export const BLUESKY_LINK = 'https://bsky.app/profile/beeaiagents.bsky.social';

export const APP_NAME = 'BeeAI';
