import { createBackendModule } from '@backstage/backend-plugin-api';
import {
  authProvidersExtensionPoint,
  createOAuthProviderFactory,
} from '@backstage/plugin-auth-node';
import { oidcAuthenticator } from '@backstage/plugin-auth-backend-module-oidc-provider';

/**
 * Sign-in for people who authenticated at Dex.
 *
 * Dex hands us the claims of whatever identity provider it federates (GitHub in production). We map the person onto a
 * `User` entity of the catalog, so ownership and permissions follow the catalog:
 *   1. `preferred_username` (the GitHub login) -> `user:default/<login>`; this is also how the GitHub organisation
 *      provider names the users it imports;
 *   2. otherwise the email address -> the User whose `spec.profile.email` matches.
 * Somebody who is not in the catalog cannot sign in (no `dangerouslyAllowSignInWithoutUserInCatalog`): the organisation
 * decides who is a user by membership, not by who happens to hold a GitHub account.
 */
export default createBackendModule({
  pluginId: 'auth',
  moduleId: 'dex-sign-in',
  register(reg) {
    reg.registerInit({
      deps: { providers: authProvidersExtensionPoint },
      async init({ providers }) {
        providers.registerProvider({
          providerId: 'oidc',
          factory: createOAuthProviderFactory({
            authenticator: oidcAuthenticator,
            async signInResolver({ result }, ctx) {
              const login = result.fullProfile.userinfo.preferred_username
                ?.toString()
                .toLowerCase();
              const email = result.fullProfile.userinfo.email?.toLowerCase();

              if (login) {
                try {
                  return await ctx.signInWithCatalogUser({
                    entityRef: { kind: 'User', namespace: 'default', name: login },
                  });
                } catch {
                  // fall through to the email lookup
                }
              }
              if (email) {
                return await ctx.signInWithCatalogUser({
                  filter: { 'spec.profile.email': email },
                });
              }
              throw new Error(
                'Dex returned neither a login nor an email for this person; cannot map them to a catalog User',
              );
            },
          }),
        });
      },
    });
  },
});
