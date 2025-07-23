/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { memo, useMemo } from 'react';

import { ExternalLink } from '#components/MarkdownContent/components/ExternalLink.tsx';
import { Tooltip } from '#components/Tooltip/Tooltip.tsx';

import type { AgentAuthor, AgentContributor } from '../api/types';
import classes from './AgentCredits.module.scss';

interface Props {
  author?: AgentAuthor;
  contributors?: AgentContributor[];
}

export const AgentCredits = memo(function AgentCredits({ author, contributors }: Props) {
  const validContributors = useMemo(
    () => contributors?.filter(({ name, email }) => Boolean(name || email)),
    [contributors],
  );

  if (!author && !validContributors?.length) {
    return null;
  }

  return (
    <div className={classes.root}>
      <span>
        {!author ? (
          <em className={classes.noAuthor}>No author</em>
        ) : (
          <>
            By <AuthorView name={author.name} email={author.email} />
          </>
        )}
      </span>

      {validContributors?.length && (
        <div className={classes.contributors}>
          (+
          <ul>
            {validContributors.map((contributor, idx) => (
              <li key={idx}>
                <AuthorView {...contributor} />
              </li>
            ))}
          </ul>
          )
        </div>
      )}
    </div>
  );
});

function AuthorView({ name, email, url }: AgentContributor) {
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
