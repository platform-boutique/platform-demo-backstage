import { createBackend } from '@backstage/backend-defaults';
import { argocdServiceFactory } from '@roadiehq/backstage-plugin-argo-cd-backend';

const backend = createBackend();

// Serves the compiled frontend and the API from one origin
backend.add(import('@backstage/plugin-app-backend'));
backend.add(import('@backstage/plugin-proxy-backend'));

// Authentication: Dex (OpenID Connect) is the only way in. The sign-in resolver is our own module.
// https://backstage.io/docs/auth/oidc
backend.add(import('@backstage/plugin-auth-backend'));
backend.add(import('./modules/dexSignIn'));

// Software catalog: descriptors from GitHub (production) or the mounted workspace (kind demo)
// https://backstage.io/docs/features/software-catalog/
backend.add(import('@backstage/plugin-catalog-backend'));
backend.add(import('@backstage/plugin-catalog-backend-module-logs'));
// https://backstage.io/docs/integrations/github/discovery
backend.add(import('@backstage/plugin-catalog-backend-module-github'));
// https://backstage.io/docs/integrations/github/org
backend.add(import('@backstage/plugin-catalog-backend-module-github-org'));

// TechDocs: builds MkDocs sites from the repositories' docs/ folders
// https://backstage.io/docs/features/techdocs/
backend.add(import('@backstage/plugin-techdocs-backend'));

// Kubernetes: read-only view of workloads
// https://backstage.io/docs/features/kubernetes/
backend.add(import('@backstage/plugin-kubernetes-backend'));

// Argo CD (Roadie): talks to Argo CD's API with a read-only token
backend.add(argocdServiceFactory);
backend.add(import('@roadiehq/backstage-plugin-argo-cd-backend'));

// Kyverno policy findings per workload and the policy catalog (own plugin, platform-demo-backstage-plugin-policies)
backend.add(import('@platform-boutique/backstage-plugin-policies-backend'));

// Network flows from Hubble Relay (own plugin, platform-demo-backstage-plugin-hubble)
backend.add(import('@platform-boutique/backstage-plugin-hubble-backend'));

// Release state: what Argo CD runs vs. what the Helm repository declares (own plugin, platform-demo-backstage-plugin-releases)
backend.add(import('@platform-boutique/backstage-plugin-releases-backend'));

// Permissions: allow-all (every signed-in person may see everything; the portal is read-only for infrastructure).
// https://backstage.io/docs/permissions/getting-started
backend.add(import('@backstage/plugin-permission-backend'));
backend.add(
  import('@backstage/plugin-permission-backend-module-allow-all-policy'),
);

// Search over catalog and docs (PostgreSQL full text search)
// https://backstage.io/docs/features/search/
backend.add(import('@backstage/plugin-search-backend'));
backend.add(import('@backstage/plugin-search-backend-module-pg'));
backend.add(import('@backstage/plugin-search-backend-module-catalog'));
backend.add(import('@backstage/plugin-search-backend-module-techdocs'));

// Per-user settings (starred entities, theme); the frontend's storage API talks to the signals service to sync tabs
backend.add(import('@backstage/plugin-user-settings-backend'));
backend.add(import('@backstage/plugin-signals-backend'));

backend.start();
