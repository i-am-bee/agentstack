/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import '../styles/style.scss';

import DefaultPage from 'keycloakify/login/DefaultPage';
import { lazy, Suspense } from 'react';

import { useI18n } from '../login/i18n';
import type { KcContext } from '../login/KcContext';
import { useApplyThemeScript } from './hooks/useApplyThemeScript';
import Template from './layout/Template';

const UserProfileFormFields = lazy(() => import('./components/UserProfileForm/UserProfileFormFields'));
const Code = lazy(() => import('./pages/Code'));
const DeleteAccountConfirm = lazy(() => import('./pages/DeleteAccountConfirm'));
const DeleteCredential = lazy(() => import('./pages/DeleteCredential'));
const Error = lazy(() => import('./pages/Error'));
const IdpReviewUserProfile = lazy(() => import('./pages/IdpReviewUserProfile'));
const Info = lazy(() => import('./pages/Info'));
const LinkIdpAction = lazy(() => import('./pages/LinkIdpAction'));
const Login = lazy(() => import('./pages/Login'));
const LoginIdpLinkConfirm = lazy(() => import('./pages/LoginIdpLinkConfirm'));
const LoginIdpLinkConfirmOverride = lazy(() => import('./pages/LoginIdpLinkConfirmOverride'));
const LoginIdpLinkEmail = lazy(() => import('./pages/LoginIdpLinkEmail'));
const LoginPageExpired = lazy(() => import('./pages/LoginPageExpired'));
const LoginPassword = lazy(() => import('./pages/LoginPassword'));
const LoginResetPassword = lazy(() => import('./pages/LoginResetPassword'));
const LoginUpdatePassword = lazy(() => import('./pages/LoginUpdatePassword'));
const LoginUpdateProfile = lazy(() => import('./pages/LoginUpdateProfile'));
const LoginUsername = lazy(() => import('./pages/LoginUsername'));
const LoginVerifyEmail = lazy(() => import('./pages/LoginVerifyEmail'));
const LogoutConfirm = lazy(() => import('./pages/LogoutConfirm'));
const Register = lazy(() => import('./pages/Register'));
const Terms = lazy(() => import('./pages/Terms'));
const UpdateEmail = lazy(() => import('./pages/UpdateEmail'));

const doMakeUserConfirmPassword = true;

export default function KcPage(props: { kcContext: KcContext }) {
  const { kcContext } = props;

  const { i18n } = useI18n({ kcContext });

  useApplyThemeScript();

  return (
    <Suspense>
      {(() => {
        switch (kcContext.pageId) {
          case 'login.ftl':
            return <Login kcContext={kcContext} i18n={i18n} />;
          case 'login-username.ftl':
            return <LoginUsername kcContext={kcContext} i18n={i18n} />;
          case 'login-password.ftl':
            return <LoginPassword kcContext={kcContext} i18n={i18n} />;
          case 'register.ftl':
            return <Register kcContext={kcContext} i18n={i18n} doMakeUserConfirmPassword={doMakeUserConfirmPassword} />;

          case 'login-update-profile.ftl':
            return (
              <LoginUpdateProfile
                kcContext={kcContext}
                i18n={i18n}
                doMakeUserConfirmPassword={doMakeUserConfirmPassword}
              />
            );
          case 'update-email.ftl':
            return (
              <UpdateEmail kcContext={kcContext} i18n={i18n} doMakeUserConfirmPassword={doMakeUserConfirmPassword} />
            );
          case 'login-update-password.ftl':
            return <LoginUpdatePassword kcContext={kcContext} i18n={i18n} />;
          case 'terms.ftl':
            return <Terms kcContext={kcContext} i18n={i18n} />;
          case 'error.ftl':
            return <Error kcContext={kcContext} i18n={i18n} />;
          case 'info.ftl':
            return <Info kcContext={kcContext} i18n={i18n} />;
          case 'code.ftl':
            return <Code kcContext={kcContext} i18n={i18n} />;
          case 'login-reset-password.ftl':
            return <LoginResetPassword kcContext={kcContext} i18n={i18n} />;
          case 'delete-account-confirm.ftl':
            return <DeleteAccountConfirm kcContext={kcContext} i18n={i18n} />;
          case 'delete-credential.ftl':
            return <DeleteCredential kcContext={kcContext} i18n={i18n} />;
          case 'idp-review-user-profile.ftl':
            return (
              <IdpReviewUserProfile
                kcContext={kcContext}
                i18n={i18n}
                doMakeUserConfirmPassword={doMakeUserConfirmPassword}
              />
            );
          case 'login-idp-link-confirm.ftl':
            return <LoginIdpLinkConfirm kcContext={kcContext} i18n={i18n} />;
          case 'login-idp-link-email.ftl':
            return <LoginIdpLinkEmail kcContext={kcContext} i18n={i18n} />;
          case 'login-page-expired.ftl':
            return <LoginPageExpired kcContext={kcContext} i18n={i18n} />;
          case 'login-verify-email.ftl':
            return <LoginVerifyEmail kcContext={kcContext} i18n={i18n} />;
          case 'logout-confirm.ftl':
            return <LogoutConfirm kcContext={kcContext} i18n={i18n} />;
          case 'link-idp-action.ftl':
            return <LinkIdpAction kcContext={kcContext} i18n={i18n} />;
          case 'login-idp-link-confirm-override.ftl':
            return <LoginIdpLinkConfirmOverride kcContext={kcContext} i18n={i18n} />;

          default:
            return (
              <DefaultPage
                kcContext={kcContext}
                i18n={i18n}
                Template={Template}
                doUseDefaultCss={true}
                UserProfileFormFields={UserProfileFormFields}
                doMakeUserConfirmPassword={doMakeUserConfirmPassword}
              />
            );
        }
      })()}
    </Suspense>
  );
}
