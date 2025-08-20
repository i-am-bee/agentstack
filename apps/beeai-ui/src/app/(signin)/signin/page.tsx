/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { redirect } from 'next/navigation';
import { AuthError } from 'next-auth';

import { providerMap, signIn } from '#auth.ts';
import { SigninButton } from '#components/SigninButton/SigninButton.tsx';

import classes from './signin.module.scss';

const SIGNIN_ERROR_URL = '/error';

export interface SigninPageProps {
  searchParams?: Promise<{ [key: string]: string | string[] | undefined }>;
}

export default async function SignInPage(props: SigninPageProps) {
  const searchParams = await props.searchParams;
  return (
    <div className={classes.bannerBackground}>
      {/* <BannerImage /> */}
      <div className={classes.loginWrapper}>
        <div className={classes.loginMain}>
          <span>Log in to </span>
          <span className={classes.bolded}>BeeAI</span>
        </div>
        <div className={classes.buttonList}>
          {Object.values(providerMap).map((provider) => (
            <form
              key={provider.id}
              action={async () => {
                'use server';
                try {
                  const callbackUrl = searchParams?.['callbackUrl'] ?? '';
                  if (typeof callbackUrl == 'string') {
                    await signIn(provider.id, {
                      redirectTo: callbackUrl,
                    });
                  } else {
                    throw new URIError('missing or invalid redirect uri passed to signIn.');
                  }
                } catch (error) {
                  // Signin can fail for a number of reasons, such as the user
                  // not existing, or the user not having the correct role.
                  // In some cases, you may want to redirect to a custom error
                  if (error instanceof AuthError) {
                    return redirect(`${SIGNIN_ERROR_URL}?error=${error.type}`);
                  }

                  // Otherwise if a redirects happens Next.js can handle it
                  // so you can just re-thrown the error and let Next.js handle it.
                  // Docs:
                  // https://nextjs.org/docs/app/api-reference/functions/redirect#server-component
                  throw error;
                }
              }}
            >
              <div className={classes.beeaiLogin}>
                <SigninButton provider={provider} />
              </div>
            </form>
          ))}
        </div>
      </div>
    </div>
  );
}
