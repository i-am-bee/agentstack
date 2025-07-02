#!/usr/bin/env -S npx -y tsx@latest
/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */


import { Monitor } from "@i-am-bee/beekeeper/ui/monitor.js";
import { OUTPUT_DIR } from "./supervisor.js";
import process from 'process';
import { Logger } from "beeai-framework";

// Get output directory from command line args if provided
// The first two arguments are node and script name, so we check for the third
const cmdOutputDir = process.argv[2];

// Use command line arg if provided, otherwise fall back to imported OUTPUT_DIR
const outputDir = cmdOutputDir || OUTPUT_DIR;

new Monitor("Supervisor", Logger.root.child({ name: 'supervisor' })).start(outputDir);
