/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { OIDCConfig } from 'next-auth/providers/index';
/**
 * Add IBM login to your page.
 *
 * ### Setup
 *
 * #### Callback URL
 * ```
 * https://example.com/api/auth/callback/IBM
 * ```
 *
 * #### Configuration
 *```ts
 * import { Auth } from "@auth/core"
 * import IBM from "@auth/core/providers/IBM"
 *
 * const request = new Request(origin)
 * const response = await Auth(request, {
 *   providers: [
 *     IBM({ clientId: IBM_CLIENT_ID, clientSecret: IBM_CLIENT_SECRET }),
 *   ],
 * })
 * ```
 *
 * ### Resources
 *
 *  - [IBM OAuth documentation](https://cloud.ibm.com/)
 *  - [IBM OAuth Configuration](https://cloud.ibm.com/)
 *
 * ### Notes
 *
 * By default, Auth.js assumes that the IBM provider is
 * based on the [Open ID Connect](https://openid.net/specs/openid-connect-core-1_0.html) specification.
 *
 *
 * The "Authorized redirect URIs" used when creating the credentials must include your full domain and end in the callback path. For example;
 *
 * - For production: `https://{YOUR_DOMAIN}/api/auth/callback/IBM`
 * - For development: `https://localhost:3000/api/auth/callback/IBM`
 *
 *
 * ```ts
 * const options = {
 *   providers: [
 *     IBM({
 *       clientId: process.env.IBM_ID,
 *       clientSecret: process.env.IBM_SECRET,
 *       authorization: {
 *         params: {
 *           prompt: "consent",
 *           access_type: "offline",
 *           response_type: "code"
 *         }
 *       }
 *     })
 *   ],
 * }
 * ```
 *
 * :::
 *
 * ```ts
 * const options = {
 *   ...
 *   callbacks: {
 *     async signIn({ account, profile }) {
 *       if (account.provider === "IBM") {
 *         return profile.email_verified && profile.email.endsWith("@example.com")
 *       }
 *       return true // Do different verification for other providers that don't have `email_verified`
 *     },
 *   }
 *   ...
 * }
 * ```
 *
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export interface IbmProfile extends Record<string, any> {
  lastName: string;
  email_verified: boolean;
  realmName: string;
  displayName: string;
  dn: string;
  preferred_username: string;
  cn: string;
  middle_name: string;
  given_name: string;
  uid: string;
  firstName: string;
  emailAddress: string;
  name: string;
  family_name: string;
  email: string;
  userType: string;
  uniqueSecurityName: number;
  auth_time: number;
  sub: string;
  ext: {
    tenantId: string;
  };
  iss: string;
  aud: string;
  iat: number;
  exp: number;
}

export function IBMProvider(config: OIDCConfig<IbmProfile>): OIDCConfig<IbmProfile> {
  return {
    id: config.id,
    name: config.name,
    type: 'oidc',
    idToken: true,
    style: { text: '#ffffff', bg: '#252525' },
    options: config,
    token: `${process.env.NEXTAUTH_URL}/auth/token-proxy/${config.id}`,
  };
}
