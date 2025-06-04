/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { LineClampText } from '#components/LineClampText/LineClampText.tsx';

import type { Agent } from '../api/types';
import classes from './AgentTools.module.scss';

interface Props {
  agent: Agent;
}

export function AgentTools({ agent }: Props) {
  const tools = agent.metadata.annotations?.tools;

  return (
    <div className={classes.root}>
      {tools?.length ? (
        <ul>
          {tools.map(({ name, description }, idx) => (
            <li key={idx}>
              <span className={classes.name}>{name}</span>
              <LineClampText className={classes.description} buttonClassName={classes.viewMore} lines={3}>
                {description}
              </LineClampText>
            </li>
          ))}
        </ul>
      ) : (
        <p className={classes.empty}>This agent does not have any tools</p>
      )}
    </div>
  );
}
