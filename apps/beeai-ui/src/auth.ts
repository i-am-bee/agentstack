/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { readFile } from 'fs/promises';
import NextAuth, { type DefaultSession } from 'next-auth';
import type { Provider } from 'next-auth/providers';
import Credentials from 'next-auth/providers/credentials';

import { ProviderList } from '#app/auth/providers/providerlist.ts';

let provider_list: {
  id: string;
  name: string;
  type: 'oidc';
  issuer: string;
  client_id: string;
  client_secret: string;
  nextauth_redirect_proxy_url: string;
}[] = [];
if (!process.env.NEXT__DISABLE_OIDC) {
  const rootPath = process.env.OIDC__PROVIDERS_PATH || './providers';
  try {
    provider_list = JSON.parse(await readFile(`${rootPath}/providers.json`, 'utf8'));
  } catch (parse_err) {
    console.warn(
      `Unable to parse provider list: ${rootPath}/providers.json.  Missing, not found, or invalid JSON. error: `,
    );
    console.error(parse_err);
  }
}

declare module 'next-auth' {
  /**
   * Returned by `auth`, `useSession`, `getSession` and received as a prop on the `SessionProvider` React Context
   */
  interface Session {
    id_token: string & DefaultSession['user'];
  }
}

import type { JWT, JWTDecodeParams, JWTEncodeParams } from 'next-auth/jwt';

declare module 'next-auth/jwt' {
  /** Returned by the `jwt` callback and `auth`, when using JWT sessions */
  interface JWT {
    /** OpenID ID Token */
    id_token?: string;
  }
}
// The providers come from a secret "oidc-providers" whos data is JSON and mounted in fs and loaded via import as json
const providers: Provider[] = [
  Credentials({
    credentials: { password: { label: 'Password', type: 'password' } },
    authorize(c) {
      if (c.password !== 'password') return null;
      return {
        id: 'test',
        name: 'Test User',
        email: 'test@example.com',
      };
    },
  }),
];

if (process.env.NEXTAUTH_SECRET) {
  const pList = new ProviderList();
  for (const prov of provider_list) {
    const pClass = pList.getProviderByName(prov.name);
    providers.push(
      pClass({
        id: prov.id,
        name: prov.name,
        type: prov.type,
        issuer: prov.issuer,
        clientId: prov.client_id,
        clientSecret: prov.client_secret,
        redirectProxyUrl: prov.nextauth_redirect_proxy_url,
        account(account: {
          refresh_token_expires_in: string;
          access_token: string;
          expires_at: string;
          refresh_token: string;
        }) {
          const refresh_token_expires_at = Math.floor(Date.now() / 1000) + Number(account.refresh_token_expires_in);
          return {
            access_token: account.access_token,
            expires_at: account.expires_at,
            refresh_token: account.refresh_token,
            refresh_token_expires_at,
          };
        },
      }),
    );
  }
}

export const providerMap = providers
  .map((provider) => {
    if (typeof provider === 'function') {
      const providerData = provider();
      return { id: providerData.id, name: providerData.name };
    } else {
      return { id: provider.id, name: provider.name };
    }
  })
  .filter((provider) => provider.id !== 'credentials');

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers,
  pages: {
    signIn: '/signin',
  },
  basePath: '/auth',
  session: { strategy: 'jwt' },
  trustHost: true,
  useSecureCookies: true,
  jwt: {
    async encode(params: JWTEncodeParams<JWT>): Promise<string> {
      // return a custom encoded JWT string
      return params?.token?.['id_token'] || '';
    },
    async decode(params: JWTDecodeParams): Promise<JWT | null> {
      // return a `JWT` object, or `null` if decoding failed
      // likely need to base64 decode the id_token and extract the
      const jwt = { id_token: params.token || '' };
      return jwt;
    },
  },
  cookies: {
    sessionToken: {
      name: `beeai-platform`,
      options: {
        httpOnly: true,
        sameSite: 'lax',
        path: '/',
        secure: true,
      },
    },
  },
  callbacks: {
    // middleware callback
    authorized({ request, auth }) {
      // essentially return !!auth
      const isOidcDisabled = process.env.NEXT__DISABLE_OIDC === 'true';
      if (isOidcDisabled) {
        return true;
      }
      const { pathname } = request.nextUrl;
      if (pathname === '/') return !!auth;
      return !!auth;
    },
    jwt({ token, account, trigger, session }) {
      if (trigger === 'update') {
        token.name = session.user.name;
        if (token['id_token'] && session) {
          if (!session['id_token']) {
            session['id_token'] = token['id_token'];
          }
        }
      }
      // pull the id token out of the account on signIn
      if (account) {
        token['id_token'] = account.id_token;
      }
      return token;
    },
    async session({ session, token }) {
      if (token?.id_token) session['id_token'] = token.id_token;
      return session;
    },
  },
});
