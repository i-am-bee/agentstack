/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentDetailContributor } from 'agentstack-sdk';

import { ExternalLink } from '#components/MarkdownContent/components/ExternalLink.tsx';
import { Tooltip } from '#components/Tooltip/Tooltip.tsx';

import classes from './AgentCredits.module.scss';

interface Props {
  author?: AgentDetailContributor | null;
  contributors?: AgentDetailContributor[] | null;
}

export function AgentCredits({ author, contributors }: Props) {
  const validContributors = contributors?.filter(({ name, email }) => Boolean(name || email));

  const hasContributors = !!validContributors && validContributors.length > 0;

  if (!author && !hasContributors) {
    return null;
  }

  return (
    <dl className={classes.root}>
      {author && (
        <div>
          <dt>Author</dt>
          <dd>
            <AuthorView {...author} />
          </dd>
        </div>
      )}

      {hasContributors && (
        <div>
          <dt>Contributors</dt>
          <dd>
            <ul className={classes.contributors}>
              {validContributors.map((contributor, idx) => (
                <li key={idx}>
                  <AuthorView {...contributor} />
                </li>
              ))}
            </ul>
          </dd>
        </div>
      )}
    </dl>
  );
}

function AuthorView({ name, email, url }: AgentDetailContributor) {
  const displayName = name ? name : email;

  return url ? (
    <ExternalLink href={url}>{displayName}</ExternalLink>
  ) : email ? (
    <Tooltip content="Click to email" placement="bottom-start" asChild>
      <a href={`mailto:${email}`}>{displayName}</a>
    </Tooltip>
  ) : (
    displayName
  );
}
