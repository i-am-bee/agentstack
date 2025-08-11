/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import NextAuth, { type DefaultSession } from 'next-auth';
import type { Provider } from 'next-auth/providers';
import Credentials from 'next-auth/providers/credentials';

import IBM from '#app/auth/providers/ibm.ts';

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
// TODO: the providers env vars should come from a config map mounted in fs and loaded via import as json
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
  IBM({
    id: 'w3id',
    name: 'w3id',
    type: 'oidc',
    issuer: process.env.NEXTAUTH_IBM_ISSUER,
    clientId: process.env.NEXTAUTH_IBM_CLIENT_ID,
    clientSecret: process.env.NEXTAUTH_IBM_CLIENT_SECRET,
    redirectProxyUrl: process.env.NEXTAUTH_REDIRECT_PROXY_URL,
    account(account) {
      const refresh_token_expires_at = Math.floor(Date.now() / 1000) + Number(account.refresh_token_expires_in);
      return {
        access_token: account.access_token,
        expires_at: account.expires_at,
        refresh_token: account.refresh_token,
        refresh_token_expires_at,
      };
    },
  }),
  // IBM({
  //   id: 'IBMiD',
  //   name: 'IBMiD',
  //   type: 'oidc',
  //   issuer: process.env.NEXTAUTH_IBM_ISSUER_URL,
  //   clientId: process.env.NEXTAUTH_IBM_CLIENT_ID,
  //   clientSecret: process.env.NEXTAUTH_IBM_CLIENT_SECRET,
  //   redirectProxyUrl: process.env.NEXTAUTH_REDIRECT_PROXY_URL,
  //   account(account) {
  //     const refresh_token_expires_at = Math.floor(Date.now() / 1000) + Number(account.refresh_token_expires_in);
  //     return {
  //       access_token: account.access_token,
  //       expires_at: account.expires_at,
  //       refresh_token: account.refresh_token,
  //       refresh_token_expires_at,
  //     };
  //   },
  // }),
];

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
  debug: true,
  providers,
  pages: {
    signIn: '/signin',
  },
  basePath: '/auth',
  session: { strategy: 'jwt' },
  trustHost: true,
  redirectProxyUrl: process.env.NEXTAUTH_REDIRECT_PROXY_URL,
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
    authorized({ request, auth }) {
      const { pathname } = request.nextUrl;
      if (pathname === '/middleware-example') return !!auth;
      return true;
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
