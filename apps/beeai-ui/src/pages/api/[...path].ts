/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import http from 'http';
import httpProxy from 'http-proxy';
import https from 'https';
import type { NextApiRequest, NextApiResponse } from 'next';

import { createApiErrorResponse } from '#api/server-utils.ts';

// Use custom agent to enable keep alive for better perf
const agentOptions = {
  keepAlive: true,
  keepAliveMsecs: 60 * 1000, // 1 minute
};

const agents: Record<string, unknown> = {
  http: new http.Agent(agentOptions),
  https: new https.Agent(agentOptions),
};
const target = new URL(process.env.API_URL!);

const proxy = httpProxy.createProxy({
  target,
  changeOrigin: true,
  xfwd: true,
  agent: agents[target.protocol],
});

// Use api route in pages dir instead of app route handler
// because here we can access raw node request and response
// so we can use http-proxy package, which handles correctly
// request cancellation.

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // Rewrite path
  let { path } = req.query;
  if (!path) path = [];
  if (!Array.isArray(path)) path = [path];
  if (!new RegExp('^v\\d+|observe$').test(path[0])) {
    res.status(404).json(createApiErrorResponse('not_found', 'Route is not available'));
  }

  let search = '';
  const searchStart = req.url?.indexOf('?');
  if (searchStart != null && searchStart >= 0) {
    const params = new URLSearchParams(req.url?.substring(searchStart + 1));

    search = `?${params.toString()}`;
  }
  req.url = '/api/' + path.join('/') + search;

  proxy.web(req, res, {}, (err: NodeJS.ErrnoException) => {
    if (err.code === 'ECONNREFUSED') {
      res.status(503).json(createApiErrorResponse('server_error', 'Service Unavailable'));
    } else if (err.code === 'ECONNRESET') {
      res.status(504).json(createApiErrorResponse('server_error', err.message));
    } else {
      res.status(500).json(createApiErrorResponse('server_error', err.message));
    }
  });
}

export const config = {
  api: {
    bodyParser: false,
    externalResolver: true,
    responseLimit: false,
  },
};
