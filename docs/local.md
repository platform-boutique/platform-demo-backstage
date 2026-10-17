# Run it locally

Two ways: the whole platform on a laptop cluster (what the portal is for), or only the portal in development mode.

## On the laptop cluster

Needs Docker, kind, kubectl, Helm, Node 22 or 24 with Yarn 4, Python 3 and about 6.5 GB of free RAM. Nothing is pushed or run on GitHub.

```bash
# 1. build the portal image (about four minutes the first time)
cd platform-demo-backstage && docker build -t platform-demo-backstage:dev .

# 2. add the hostnames once (WSL: /etc/hosts, Windows: C:\Windows\System32\drivers\etc\hosts)
127.0.0.1 shop.platform-demo.test grafana.platform-demo.test argocd.platform-demo.test hubble.platform-demo.test backstage.platform-demo.test dex.platform-demo.test

# 3. build the cluster from this working tree (about ten minutes)
cd platform-demo-helm && LOCAL_SOURCE=1 kind/up.sh
```

`LOCAL_SOURCE=1` is what makes it work without pushing: `kind/local-source.sh` serves a staged copy of the Helm repository (as a Git
remote Argo CD can clone) and of every `catalog-info.yaml` over HTTP on the Docker network's gateway address, and
`kind/load-image.sh` puts the locally built portal image into the node. Re-run `kind/local-source.sh sync` after changing anything and
Argo CD picks it up within two minutes.

Then open <https://backstage.platform-demo.test> (trust `kind/certs/ca.crt` to remove the certificate warning) and sign in as the
demo user: `demo@platform-demo.test`, password in `kind/certs/demo-password`.

What `up.sh` does for the portal, beyond the platform itself:

| Step | Script |
|---|---|
| CoreDNS rewrite so pods reach Dex under its public name | `up.sh` |
| Namespaces, CA ConfigMap, Dex TLS Secret, random client secrets | `kind/sso-secrets.sh` |
| Image into the node, local source staged | `kind/load-image.sh`, `kind/local-source.sh` |
| Argo CD and Grafana accounts for the portal and their tokens | `kind/sso-bootstrap.sh` |
| TechDocs rendered and published | `kind/techdocs-publish.sh` |

Tear down with `kind/down.sh` (also stops the local source server).

## Only the portal, with `yarn start`

```bash
yarn install
cat > app-config.dev.yaml <<'YAML'   # git-ignored
auth:
  providers:
    oidc:
      development:
        metadataUrl: https://dex.platform-demo.test/.well-known/openid-configuration
        clientId: backstage
        clientSecret: <the secret from kubectl -n sso get secret dex-secrets>
YAML
yarn start --config ../../app-config.yaml --config ../../app-config.dev.yaml
```

Dex only accepts redirect URIs of the configured clients, so signing in from `localhost:3000` needs that URI added to the
`backstage` client in `dex/values.yaml` for your own environment. For work on plugins, an easier route is to run the plugin's own dev
setup (each plugin repository has one) against a port-forwarded service.
