/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { I18n } from "../../i18n";

interface Props {
  i18n: I18n;
}

export function LocaleNav({ i18n }: Props) {
  const { enabledLanguages } = i18n;

  if (enabledLanguages.length <= 1) {
    return null;
  }

  // TODO: Re-implement locale switcher UI
  // return (
  //   <div className={kcClsx("kcLocaleMainClass")} id='kc-locale'>
  //     <div id='kc-locale-wrapper' className={kcClsx("kcLocaleWrapperClass")}>
  //       <div
  //         id='kc-locale-dropdown'
  //         className={clsx("menu-button-links", kcClsx("kcLocaleDropDownClass"))}
  //       >
  //         <button
  //           tabIndex={1}
  //           id='kc-current-locale-link'
  //           aria-label={msgStr("languages")}
  //           aria-haspopup='true'
  //           aria-expanded='false'
  //           aria-controls='language-switch1'
  //         >
  //           {currentLanguage.label}
  //         </button>
  //         <ul
  //           role='menu'
  //           tabIndex={-1}
  //           aria-labelledby='kc-current-locale-link'
  //           aria-activedescendant=''
  //           id='language-switch1'
  //           className={kcClsx("kcLocaleListClass")}
  //         >
  //           {enabledLanguages.map(({ languageTag, label, href }, i) => (
  //             <li
  //               key={languageTag}
  //               className={kcClsx("kcLocaleListItemClass")}
  //               role='none'
  //             >
  //               <a
  //                 role='menuitem'
  //                 id={`language-${i + 1}`}
  //                 className={kcClsx("kcLocaleItemClass")}
  //                 href={href}
  //               >
  //                 {label}
  //               </a>
  //             </li>
  //           ))}
  //         </ul>
  //       </div>
  //     </div>
  //   </div>
  // );
}
