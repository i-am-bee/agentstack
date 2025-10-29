/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import createMDX from '@next/mdx';
import type { NextConfig } from 'next';
import path from 'path';
import rehypeSlug from 'rehype-slug';
import remarkFlexibleToc from 'remark-flexible-toc';
import remarkReadingTime from 'remark-reading-time';
import remarkReadingTimeMdx from 'remark-reading-time/mdx';

import { recmaExportToc } from '@/modules/blog/recma';

const nextConfig: NextConfig = {
  output: 'standalone',
  transpilePackages: ['@i-am-bee/agentstack-ui'],
  sassOptions: {
    additionalData: `@use 'styles/common' as *; @use 'sass:math';`,
    // silenceDeprecations: ['mixed-decls', 'global-builtin'],
    api: 'modern',
    implementation: 'sass-embedded',
    quietDeps: true,
    includePaths: [path.join(__dirname, 'node_modules'), path.join(__dirname, 'src')],
  },
  pageExtensions: ['js', 'jsx', 'md', 'mdx', 'ts', 'tsx'],
  webpack(config) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const fileLoaderRule = config.module.rules.find((rule: any) => rule.test?.test?.('.svg'));

    config.module.rules.push(
      // Reapply the existing rule, but only for svg imports ending in ?url
      {
        ...fileLoaderRule,
        test: /\.svg$/i,
        resourceQuery: /url/, // *.svg?url
      },
      // Convert all other *.svg imports to React components
      {
        test: /\.svg$/i,
        issuer: fileLoaderRule.issuer,
        resourceQuery: { not: [...fileLoaderRule.resourceQuery.not, /url/] }, // exclude if *.svg?url
        use: [
          {
            loader: '@svgr/webpack',
            options: {
              svgoConfig: {
                plugins: [
                  {
                    name: 'preset-default',
                    params: {
                      overrides: {
                        removeViewBox: false,
                      },
                    },
                  },
                ],
              },
            },
          },
        ],
      },
    );

    // Modify the file loader rule to ignore *.svg, since we have it handled now.
    fileLoaderRule.exclude = /\.svg$/i;

    return config;
  },
  experimental: {
    // Disable CSS chunking due to persistent nextjs bug with ordering of css and this seems to help partially.
    // Nextjs in production build only! puts global styles last so it messes up css specificity.
    //
    // We get css modules styles twice but atleast the second css file overwrites them in correct order.
    //
    // I think it's actually two issues, first is with sideEffects and external packages, because agentstack-ui doesn't
    // have `sideEffects: false` in package.json and I don't wanna add it because it's vite app, not a library
    // and we have single `index.ts` in it that exports everything, nextjs bundler doesn't tree shake and sees
    // all styles as required in a root layout. Having separate exports in package.json helps but doesn't mitigrate
    // the issue completely see second issue bellow.
    //
    // The second issue is IMHO when the same component is imported from the page and layout and from RSC and from
    // client component simultaneously, this breaks nextjs and as a result puts global styles after css modules styles.
    // In our codebase it's a case of a Container component. I wasn't able to refactor this cleanly hence this workaround
    //
    // https://github.com/vercel/next.js/issues/68207
    // https://github.com/vercel/next.js/issues/64921
    cssChunking: false,
  },
};

const withMDX = createMDX({
  extension: /\.(md|mdx)$/,
  options: {
    remarkPlugins: [remarkFlexibleToc, remarkReadingTime, remarkReadingTimeMdx],
    rehypePlugins: [rehypeSlug],
    recmaPlugins: [recmaExportToc],
  },
});

export default withMDX(nextConfig);
