<#import "template.ftl" as layout>
<#import "passkeys.ftl" as passkeys>
<@layout.registrationLayout displayMessage=!messagesPerField.existsError('username','password') displayInfo=realm.password && realm.registrationAllowed && !registrationDisabled??; section>
    <#if section = "header">
        <#--  Header content moved inside the card for a unified look  -->
    <#elseif section = "form">
        <div class="login-card">
            <div style="margin-bottom: 2rem; text-align: center; width: 100%;">
                <img src="${url.resourcesPath}/img/logo.svg" alt="Agentstack" style="height: 60px; width: auto;">
            </div>
            <div id="kc-form" style="width: 100%;">
              <div id="kc-form-wrapper">
                <#if realm.password>
                    <form id="kc-form-login" onsubmit="login.disabled = true; return true;" action="${url.loginAction}" method="post">
                        <#if !usernameHidden??>
                            <div class="bx--form-item">
                                <label for="username" class="bx--label"><#if !realm.loginWithEmailAllowed>${msg("username")}<#elseif !realm.registrationEmailAsUsername>${msg("usernameOrEmail")}<#else>${msg("email")}</#if></label>
                                <div class="bx--text-input__field-wrapper">
                                    <input tabindex="2" id="username" class="bx--text-input <#if messagesPerField.existsError('username','password')>bx--text-input--invalid</#if>" name="username" value="${(login.username!'')}"  type="text"
                                           autofocus autocomplete="${(enableWebAuthnConditionalUI?has_content)?then('username webauthn', 'username')}"
                                           aria-invalid="<#if messagesPerField.existsError('username','password')>true</#if>"
                                           dir="ltr"
                                    />
                                    <#if messagesPerField.existsError('username','password')>
                                        <div class="bx--form-requirement">
                                            ${kcSanitize(messagesPerField.getFirstError('username','password'))?no_esc}
                                        </div>
                                    </#if>
                                </div>
                            </div>
                        </#if>

                        <div class="bx--form-item">
                            <label for="password" class="bx--label">${msg("password")}</label>
                            <div class="bx--text-input__field-wrapper" data-password-toggle>
                                <input tabindex="3" id="password" class="bx--text-input <#if messagesPerField.existsError('username','password')>bx--text-input--invalid</#if>" name="password" type="password" autocomplete="current-password"
                                       aria-invalid="<#if messagesPerField.existsError('username','password')>true</#if>"
                                />
                                <#--  We might need custom JS for password visibility toggle in Carbon, omitting complex toggle button for now to ensure basic functionality first, 
                                      or we can use the Carbon button if we add the JS. For now, simple password input. -->
                                <#if usernameHidden?? && messagesPerField.existsError('username','password')>
                                    <div class="bx--form-requirement">
                                        ${kcSanitize(messagesPerField.getFirstError('username','password'))?no_esc}
                                    </div>
                                </#if>
                            </div>
                        </div>

                        <div class="bx--form-item">
                            <div id="kc-form-options">
                                <#if realm.rememberMe && !usernameHidden??>
                                    <div class="bx--checkbox-wrapper">
                                        <#if login.rememberMe??>
                                            <input tabindex="5" id="rememberMe" class="bx--checkbox" name="rememberMe" type="checkbox" checked>
                                        <#else>
                                            <input tabindex="5" id="rememberMe" class="bx--checkbox" name="rememberMe" type="checkbox">
                                        </#if>
                                        <label for="rememberMe" class="bx--checkbox-label">${msg("rememberMe")}</label>
                                    </div>
                                </#if>
                            </div>
                            <div class="${properties.kcFormOptionsWrapperClass!}">
                                <#if realm.resetPasswordAllowed>
                                    <div style="margin-top: 0.5rem; text-align: right;">
                                        <a tabindex="6" href="${url.loginResetCredentialsUrl}" class="bx--link">${msg("doForgotPassword")}</a>
                                    </div>
                                </#if>
                            </div>
                        </div>

                          <div id="kc-form-buttons" class="bx--form-item" style="margin-top: 2rem;">
                              <input type="hidden" id="id-hidden-input" name="credentialId" <#if auth.selectedCredential?has_content>value="${auth.selectedCredential}"</#if>/>
                              <button tabindex="7" class="bx--btn bx--btn--primary" name="login" id="kc-login" type="submit">
                                ${msg("doLogIn")}
                              </button>
                          </div>
                    </form>
                </#if>
                </div>
            </div>
            
            <#-- Social Providers Section inside the card -->
            <#if realm.password && social?? && social.providers?has_content>
                <div class="social-providers">
                    <div style="margin-bottom: 1rem; color: #525252; font-size: 0.875rem;">${msg("identity-provider-login-label")}</div>
                    <ul>
                        <#list social.providers as p>
                            <li>
                                <a id="social-${p.alias}" class="social-provider-btn" type="button" href="${p.loginUrl}">
                                    <#if p.iconClasses?has_content>
                                        <i class="${properties.kcCommonLogoIdP!} ${p.iconClasses!}" aria-hidden="true"></i>
                                        <span class="social-icon-text">${p.displayName!}</span>
                                    <#else>
                                        <span class="social-icon-text">${p.displayName!}</span>
                                    </#if>
                                </a>
                            </li>
                        </#list>
                    </ul>
                </div>
            </#if>
            
             <#if realm.password && realm.registrationAllowed && !registrationDisabled??>
                <div style="margin-top: 2rem; border-top: 1px solid #e0e0e0; padding-top: 1rem; text-align: center;">
                    <span>${msg("noAccount")} <a tabindex="8" href="${url.registrationUrl}" class="bx--link">${msg("doRegister")}</a></span>
                </div>
            </#if>

        </div>
        <@passkeys.conditionalUIData />
    </#if>
    <#-- We ignore 'info' and 'socialProviders' sections from the macro loop here because we manually included them in the form section to keep them inside the card -->
</@layout.registrationLayout>
