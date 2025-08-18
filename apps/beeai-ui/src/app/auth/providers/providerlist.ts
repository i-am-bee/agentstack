/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
import Apple from 'next-auth/providers/apple';
// import Atlassian from "next-auth/providers/atlassian"
import Auth0 from 'next-auth/providers/auth0';
import AzureB2C from 'next-auth/providers/azure-ad-b2c';
import BankIDNorway from 'next-auth/providers/bankid-no';
import BoxyHQSAML from 'next-auth/providers/boxyhq-saml';
import Cognito from 'next-auth/providers/cognito';
import Coinbase from 'next-auth/providers/coinbase';
import Discord from 'next-auth/providers/discord';
import Dropbox from 'next-auth/providers/dropbox';
import Facebook from 'next-auth/providers/facebook';
import GitHub from 'next-auth/providers/github';
import GitLab from 'next-auth/providers/gitlab';
import Google from 'next-auth/providers/google';
import Hubspot from 'next-auth/providers/hubspot';
import Keycloak from 'next-auth/providers/keycloak';
import LinkedIn from 'next-auth/providers/linkedin';
import MicrosoftEntraId from 'next-auth/providers/microsoft-entra-id';
import Netlify from 'next-auth/providers/netlify';
import Okta from 'next-auth/providers/okta';
import Passage from 'next-auth/providers/passage';
import Passkey from 'next-auth/providers/passkey';
import Pinterest from 'next-auth/providers/pinterest';
import Reddit from 'next-auth/providers/reddit';
import Salesforce from 'next-auth/providers/salesforce';
import Slack from 'next-auth/providers/slack';
import Spotify from 'next-auth/providers/spotify';
import Twitch from 'next-auth/providers/twitch';
import Twitter from 'next-auth/providers/twitter';
import Vipps from 'next-auth/providers/vipps';
import WorkOS from 'next-auth/providers/workos';
import Zoom from 'next-auth/providers/zoom';

import IBM from '#app/auth/providers/ibm.ts';

export class ProviderList {
  providerMap = new Map();
  static providerNames: string[] = [
    'apple',
    'auth0',
    'azureb2c',
    'boxyhqsaml',
    'bankidnorwary',
    'cognito',
    'coinbase',
    'discord',
    'dropbox',
    'facebook',
    'github',
    'gitlab',
    'google',
    'ibm',
    'ibmid',
    'hubspot',
    'keycloak',
    'linkedin',
    'microsoftentraid',
    'netlify',
    'okta',
    'passage',
    'passkey',
    'pinterest',
    'reddit',
    'salesforce',
    'slack',
    'spotify',
    'twich',
    'twitter',
    'vipps',
    'w3id',
    'workos',
    'zoom',
  ];
  constructor() {
    function getProviderFromName(name: string) {
      switch (name.toLocaleLowerCase()) {
        case 'w3id':
          return IBM;
        case 'ibmid':
          return IBM;
        case 'ibm':
          return IBM;
        case 'apple':
          return Apple;
        case 'auth0':
          return Auth0;
        case 'azureb2c':
          return AzureB2C;
        case 'bankidnorwary':
          return BankIDNorway;
        case 'boxyhqsaml':
          return BoxyHQSAML;
        case 'cognito':
          return Cognito;
        case 'coinbase':
          return Coinbase;
        case 'discord':
          return Discord;
        case 'dropbox':
          return Dropbox;
        case 'facebook':
          return Facebook;
        case 'github':
          return GitHub;
        case 'gitlab':
          return GitLab;
        case 'google':
          return Google;
        case 'hubspot':
          return Hubspot;
        case 'keycloak':
          return Keycloak;
        case 'linkedin':
          return LinkedIn;
        case 'microsoftentraid':
          return MicrosoftEntraId;
        case 'netlify':
          return Netlify;
        case 'okta':
          return Okta;
        case 'passage':
          return Passage;
        case 'passkey':
          return Passkey;
        case 'pinterest':
          return Pinterest;
        case 'reddit':
          return Reddit;
        case 'salesforce':
          return Salesforce;
        case 'slack':
          return Slack;
        case 'spotify':
          return Spotify;
        case 'twich':
          return Twitch;
        case 'twitter':
          return Twitter;
        case 'vipps':
          return Vipps;
        case 'workos':
          return WorkOS;
        case 'zoom':
          return Zoom;
        default:
          return IBM;
      }
    }
    for (const provName of ProviderList.providerNames) {
      this.providerMap.set(provName, getProviderFromName(provName));
    }
  }
  public getProviderByName(name: string) {
    return this.providerMap.get(name);
  }
}
