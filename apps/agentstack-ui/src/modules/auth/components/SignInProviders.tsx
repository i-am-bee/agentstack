/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { redirect } from 'next/navigation';
import { AuthError } from 'next-auth';

import { authProviders, signIn } from '#app/(auth)/auth.ts';
import { routes } from '#utils/router.ts';

import { SignInButton } from './SignInButton';
import classes from './SignInProviders.module.scss';

interface Props {
  callbackUrl?: string;
}

export function SignInProviders({ callbackUrl: redirectTo = routes.home() }: Props) {
  const providers = Object.values(authProviders);

  return (
    <div className={classes.root}>
      {providers.map((provider) => {
        const { id } = provider;

        return (
          <form key={id} action={handleSignIn.bind(null, { providerId: id, redirectTo })}>
            <SignInButton provider={provider} />
          </form>
        );
      })}
    </div>
  );
}

async function handleSignIn({ providerId, redirectTo }: { providerId: string; redirectTo: string }) {
  'use server';

  try {
    await signIn(providerId, { redirectTo });
  } catch (error) {
    // Sign-in can fail for a number of reasons, such as the user not existing, or the user not having the correct role.
    // In some cases, you may want to redirect to a custom error.
    if (error instanceof AuthError) {
      return redirect(routes.error({ error }));
    }

    // Otherwise if a redirect happens Next.js can handle it so you can just re-thrown the error and let Next.js handle it.
    // https://nextjs.org/docs/app/api-reference/functions/redirect#server-component
    throw error;
  }
}
