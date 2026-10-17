#!/usr/bin/env python3
"""Scaffold catalog-info.yaml + TechDocs for the repositories that are not services (see scaffold.py for the services).

    helm            platform-demo-helm           README split + the policies / GitOps / kind READMEs included by reference
    workflows       platform-demo-workflows      README split
    docs            platform-demo-docs           the master reference split into one page per chapter, plus handoff and history
    observability   platform-demo-observability  written here (the repository had no README)
    org             .github                      written here

The Backstage repository's own docs are plain hand-written files in its docs/ folder.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scaffold import (ARGOCD, GRAFANA, HERE, ORG, WORKSPACE, fix_links, mk_slug, mkdocs_yml, one_line,  # noqa: E402
                      read_sections, slug, yq)


def write_site(repo_dir: Path, repo: str, site_name: str, description: str, pages: dict[str, str],
               nav: list[tuple[str, str]], catalog: str) -> None:
    docs = repo_dir / "docs"
    (docs / "stylesheets").mkdir(parents=True, exist_ok=True)
    shutil.copy(HERE / "extra.css", docs / "stylesheets" / "extra.css")
    for name, body in pages.items():
        (docs / name).parent.mkdir(parents=True, exist_ok=True)
        (docs / name).write_text(body)
    (repo_dir / "mkdocs.yml").write_text(mkdocs_yml(site_name, site_name, description, nav, repo))
    (repo_dir / "catalog-info.yaml").write_text(catalog)
    print(f"{repo}: {len(pages)} pages")


def split(readme: Path, repo: str, plan: list[tuple[str, str, list[str]]]):
    """Split a README into pages. plan = [(file, title, [heading prefixes])]. Returns (lead, pages, anchors)."""
    title, lead, sections = read_sections(readme)
    anchors: dict[str, tuple[str, str]] = {}
    claimed: dict[str, list[str]] = {}
    for page, _t, prefixes in plan:
        for h in sections:
            if any(h.startswith(p) for p in prefixes) and h not in sum(claimed.values(), []):
                claimed.setdefault(page, []).append(h)
                anchors[slug(h)] = (page, mk_slug(h))
    pages = {}
    for page, ptitle, _ in plan:
        heads = claimed.get(page, [])
        if not heads:
            continue
        if len(heads) == 1:
            body = f"# {ptitle}\n\n{sections[heads[0]]}\n"
        else:
            body = f"# {ptitle}\n\n" + "\n".join(f"## {h}\n\n{sections[h]}\n" for h in heads)
        pages[page] = fix_links(body, repo, anchors, page)
    return lead, pages, anchors, sections


def hero(kicker: str, text: str) -> str:
    return f'<div class="pd-hero" markdown>\n<span class="pd-kicker">{kicker}</span>\n\n{text}\n</div>\n'


def facts(items: list[tuple[str, str, str]]) -> str:
    rows = "\n".join(f"<div><span>{a}</span><strong>{b}</strong><small>{c}</small></div>" for a, b, c in items)
    return f'<div class="pd-facts" markdown>\n{rows}\n</div>\n'


def cards(items: list[tuple[str, str, str]]) -> str:
    rows = "\n".join(f'<div><h4><a href="{u}">{t}</a></h4><p>{d}</p></div>' for t, d, u in items)
    return f'<div class="pd-cards" markdown>\n{rows}\n</div>\n'


def component(name: str, title: str, desc: str, repo: str, ctype: str, system: str, ann: list[str], tags: list[str],
              links: list[tuple[str, str, str]], deps: list[str] = (), extra: str = "") -> str:
    ann_l = "\n".join(f"    {a}" for a in [f"github.com/project-slug: {ORG}/{repo}", "backstage.io/techdocs-ref: dir:."] + ann)
    links_l = "\n".join(f'    - {{ url: "{u}", title: "{t}", icon: {i} }}' for t, u, i in
                        [("Repository", f"https://github.com/{ORG}/{repo}", "github")] + links)
    dep = ("  dependsOn:\n" + "\n".join(f"    - {d}" for d in deps) + "\n") if deps else ""
    return f"""apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: {name}
  title: {title}
  description: {yq(desc)}
  annotations:
{ann_l}
  tags: [{', '.join(tags)}]
  links:
{links_l}
spec:
  type: {ctype}
  lifecycle: experimental
  owner: group:default/maintainers
  system: {system}
{dep}{extra}""".rstrip() + "\n"


# --------------------------------------------------------------------------------------------------------- helm
def helm() -> None:
    d = WORKSPACE / "deploy/platform-demo-helm"
    plan = [
        ("how-it-fits.md", "How it fits together", ["How it fits together"]),
        ("layout.md", "Repository layout", ["Layout"]),
        ("quick-start.md", "Quick start", ["Quick start"]),
        ("promote.md", "Promote an image", ["Promote an image"]),
        ("charts.md", "What each chart provides", ["What each chart provides"]),
        ("develop.md", "Configure, develop, verify", ["Configuring", "Develop", "Verified"]),
    ]
    lead, pages, _, _ = split(d / "README.md", "platform-demo-helm", plan)
    pages["index.md"] = f"""# platform-demo-helm

{hero("deploy · platform-demo", lead.split(chr(10) * 2)[0])}
{facts([("Deploys with", "Argo CD", "ApplicationSets, polled every 2 min"),
        ("Environments", "dev", "envs/&lt;env&gt;/ directories"),
        ("Charts", "12 workloads", "+ gateway, monitoring, policies"),
        ("Policies", "16", "Kyverno, enforced in platform-demo")])}
## Start here

{cards([("How it fits together", "Git, Argo CD, Cilium and Kyverno in one picture.", "how-it-fits/"),
        ("Quick start", "One command builds the whole local cluster.", "quick-start/"),
        ("Admission policies", "What Kyverno enforces, how to roll out and test a policy.", "policies/"),
        ("GitOps", "ApplicationSets, projects and how Argo CD manages itself.", "gitops/"),
        ("Local cluster", "The kind bootstrap, step by step.", "local-cluster/"),
        ("Single sign-on and the portal", "Dex, Backstage, and how the three UIs share one login.", "sso-and-portal/")])}
"""
    pages["policies.md"] = '--8<-- "policies/README.md"\n'
    pages["gitops.md"] = '--8<-- "gitops/README.md"\n'
    pages["local-cluster.md"] = '--8<-- "kind/README.md"\n'
    nav = [("Overview", "index.md"), ("How it fits together", "how-it-fits.md"), ("Repository layout", "layout.md"),
           ("Quick start", "quick-start.md"), ("Promote an image", "promote.md"), ("Charts", "charts.md"),
           ("Admission policies", "policies.md"), ("GitOps", "gitops.md"), ("Local cluster", "local-cluster.md"),
           ("Single sign-on and the portal", "sso-and-portal.md"), ("Configure, develop, verify", "develop.md")]
    # sso-and-portal.md is written by hand when the charts exist (docs/sso-and-portal.md), keep it if present
    existing = d / "docs" / "sso-and-portal.md"
    if not existing.exists():
        pages["sso-and-portal.md"] = "# Single sign-on and the portal\n\nWritten with the Dex and Backstage charts.\n"
    cat = component(
        "platform-demo-helm", "platform-demo-helm",
        "Helm charts, per-environment values, Argo CD configuration, Kyverno policies and the local kind cluster.",
        "platform-demo-helm", "deployment-config", "delivery",
        ["argocd/app-selector: app.kubernetes.io/part-of=platform-demo",
         "backstage.io/kubernetes-namespace: argocd"],
        ["helm", "gitops", "kyverno"],
        [("Argo CD", ARGOCD, "dashboard")],
        deps=["component:default/platform-demo-workflows", "resource:default/argocd", "resource:default/kyverno"])
    write_site(d, "platform-demo-helm", "platform-demo-helm", one_line(lead), pages, nav, cat)


# ---------------------------------------------------------------------------------------------------- workflows
def workflows() -> None:
    d = WORKSPACE / "platform/platform-demo-workflows"
    plan = [
        ("calling.md", "How a service calls them", ["How a service calls them"]),
        ("release-model.md", "Release model", ["Release model"]),
        ("dependabot.md", "Dependabot", ["Dependabot"]),
        ("changing.md", "Changing a workflow", ["Changing a workflow"]),
        ("things-to-know.md", "Things to know", ["Things to know"]),
        ("history.md", "Version history", ["Version history"]),
    ]
    lead, pages, _, _ = split(d / "README.md", "platform-demo-workflows", plan)
    pages["index.md"] = f"""# platform-demo-workflows

{hero("platform · shared CI/CD", lead.split(chr(10) * 2)[0])}
{facts([("Kind", "Reusable workflows", "workflow_call"),
        ("Pinned by", "commit SHA", "every caller"),
        ("Runs on", "pull requests", "and v* tags"),
        ("Secret scan", "gitleaks CLI", "free, checksum-pinned")])}
{cards([("Calling the workflows", "The shape of ci.yaml and release.yaml in a service.", "calling/"),
        ("Release model", "Trunk-based, semver tags, digest promotion.", "release-model/"),
        ("Changing a workflow", "The procedure that worked, step by step.", "changing/"),
        ("Things to know", "Constraints of the free plan and of Actions.", "things-to-know/")])}
"""
    nav = [("Overview", "index.md")] + [(t, p) for p, t, _ in plan if p in pages]
    cat = component(
        "platform-demo-workflows", "platform-demo-workflows",
        "Reusable CI/CD workflows shared by every repository: build, test, scan, sign and promote images; plus the tools that generate and bump them.",
        "platform-demo-workflows", "ci-library", "delivery", [], ["github-actions", "ci", "cosign"],
        [("Actions", f"https://github.com/{ORG}/platform-demo-workflows/actions", "github")],
        deps=["resource:default/docker-hub", "resource:default/github-organisation"])
    write_site(d, "platform-demo-workflows", "platform-demo-workflows", one_line(lead), pages, nav, cat)


# --------------------------------------------------------------------------------------------------------- docs
def docs_repo() -> None:
    d = WORKSPACE / "docs"
    plan = [
        ("system.md", "System at a glance", ["1. "]),
        ("architecture.md", "Architecture and request flows", ["2. "]),
        ("services.md", "Service inventory", ["3. "]),
        ("images.md", "Container images", ["4. "]),
        ("wiring.md", "Service wiring", ["5. "]),
        ("observability.md", "Observability contract", ["6. "]),
        ("kubernetes.md", "Kubernetes translation guide", ["7. "]),
        ("helm.md", "Helm charts", ["8. "]),
        ("gotchas.md", "Cross-cutting findings and gotchas", ["9. "]),
        ("local-stack.md", "Local stack (docker compose)", ["10. "]),
        ("repositories.md", "Repository map", ["11. "]),
        ("next-steps.md", "Next steps", ["12. "]),
        ("cicd.md", "CI/CD, branching and releases", ["13. "]),
    ]
    lead, pages, _, _ = split(d / "README.md", "platform-demo-docs", plan)
    pages["index.md"] = f"""# platform-demo docs

{hero("docs · master reference", "The single source of truth for the platform: what the shop is made of, how it is built, shipped, secured and observed, and what comes next.")}
{cards([("System at a glance", "The ten services, two data stores and the platform around them.", "system/"),
        ("Architecture", "Request flows for browsing and checkout.", "architecture/"),
        ("Observability", "The OTLP contract every service follows.", "observability/"),
        ("Kubernetes", "How the compose layout translates to the cluster.", "kubernetes/"),
        ("CI/CD", "Branching, releases, signing, promotion.", "cicd/"),
        ("Handoff", "Where things stand and what to do first.", "handoff/")])}
"""
    pages["handoff.md"] = (d / "HANDOFF.md").read_text()
    pages["otlp-migration.md"] = (d / "OTLP-MIGRATION-PLAN.md").read_text()
    hist = sorted((d / "history").glob("*.md"))
    for h in hist:
        pages[f"history/{h.name}"] = h.read_text()
    nav = [("Overview", "index.md")] + [(t, p) for p, t, _ in plan if p in pages]
    nav += [("Handoff", "handoff.md"), ("OTLP migration", "otlp-migration.md")]
    for h in hist:
        nav.append((h.stem.replace("HANDOFF-previous-", "History: ").replace("-", " "), f"history/{h.name}"))
    cat = component(
        "platform-demo-docs", "platform-demo-docs",
        "Master reference of the platform, the current handoff, and the history of earlier sessions.",
        "platform-demo-docs", "documentation", "developer-portal", [], ["documentation"], [])
    write_site(d, "platform-demo-docs", "platform-demo-docs", "Master reference of the platform-demo project.", pages, nav, cat)


# -------------------------------------------------------------------------------------------- observability
def observability() -> None:
    d = WORKSPACE / "platform/platform-demo-observability"
    dashboards = [("ad-service-overview", "Ad Service"), ("cart-service-overview", "Cart Service"),
                  ("checkout-service-overview", "Checkout Service"), ("currency-service-overview", "Currency Service"),
                  ("email-service-overview", "Email Service"), ("frontend-overview", "Frontend Service"),
                  ("payment-service-overview", "Payment Service"),
                  ("product-catalog-overview", "Product Catalog Service"),
                  ("recommendation-service-overview", "Recommendation Service"),
                  ("shipping-service-overview", "Shipping Service")]
    rows = "\n".join(f"| {t} | `{u}` | [open]({GRAFANA}/d/{u}) |" for u, t in dashboards)
    pages = {
        "index.md": f"""# platform-demo-observability

{hero("platform · observability", "The Grafana LGTM stack as a docker compose project, the Alloy pipeline, the provisioned datasources and the ten service dashboards. The Kubernetes version of the same stack lives in <code>platform-demo-helm/monitoring-local</code>; the dashboards are shared between the two.")}
{facts([("Metrics", "Mimir", "remote_write :9009"), ("Logs", "Loki", "native OTLP :3100"),
        ("Traces", "Tempo", "OTLP :4317, query :3200"), ("Profiles", "Pyroscope", "via Alloy :4040")])}
## Telemetry path

```mermaid
flowchart LR
  svc["10 services"] -->|"OTLP/gRPC :4317"| alloy["Alloy"]
  svc -->|"profiles :4040"| alloy
  alloy --> mimir[("Mimir")]
  alloy --> loki[("Loki")]
  alloy --> tempo[("Tempo")]
  alloy --> pyro[("Pyroscope")]
  grafana["Grafana"] -.queries.-> mimir
  grafana -.-> loki
  grafana -.-> tempo
  grafana -.-> pyro
```

Services push everything; nothing is scraped. `service.name` becomes the Prometheus `job` and Loki `service_name`, which is
what every dashboard filters on. The contract is described in the
[master reference](https://github.com/{ORG}/platform-demo-docs) (observability contract).

## What is in this repository

| Path | Purpose |
|---|---|
| `docker-compose.yaml` | Whole system plus the LGTM stack on one bridge network (original, pre-OTLP digests) |
| `docker-compose.otlp.yaml` | Overlay for the OTLP/gRPC contract; uses the `1.0.0` release images |
| `alloy/config.otlp.alloy` | OTLP receivers, batch processor, exporters to Mimir/Loki/Tempo, Pyroscope receiver |
| `grafana/provisioning/` | Datasources (`mimir`, `loki`, `tempo`, `pyroscope`) and the ten dashboards |
| `mimir/`, `loki/`, `tempo/`, `pyroscope/` | Single-binary configurations for local use |
""",
        "running.md": """# Running the stack

```bash
cd platform-demo-observability

# OTLP/gRPC stack (v1.0.0 images from Docker Hub):
docker compose -f docker-compose.yaml -f docker-compose.otlp.yaml up -d

docker compose ps
```

| What | Where |
|---|---|
| Shop | <http://localhost> (host 80 to 8080) |
| Grafana | <http://localhost:3000> (anonymous admin, local only) |
| Alloy UI | <http://localhost:12345> |
| OTLP/gRPC | `localhost:4317` |

!!! tip "Trying local code"
    Build an image under the release tag and compose uses it:
    `docker build -t mladenovskistefan/<service>:1.0.0 ../<service>`.

!!! warning "Original compose file"
    `docker-compose.yaml` on its own still pins the **pre-OTLP** digests and the old env contract. Always combine it with
    the OTLP overlay unless you are looking at the history.

Volumes: `grafana_data`, `mimir_data`, `loki_data`, `tempo_data`, `pyroscope_data`, `postgres_data`, `redis_data`.
""",
        "dashboards.md": f"""# Dashboards

One dashboard per service, provisioned from `grafana/provisioning/dashboards/`. Each carries the tag of its service, which
is how the portal finds it (`grafana/dashboard-selector: tags @> '<tag>'`).

| Dashboard | uid | Link |
|---|---|---|
{rows}

All 198 dashboard queries were run against a live stack; 186 return data and the remaining 12 are error-rate and
status-code panels that are empty simply because nothing failed.
""",
    }
    nav = [("Overview", "index.md"), ("Running the stack", "running.md"), ("Dashboards", "dashboards.md")]
    cat = component(
        "platform-demo-observability", "platform-demo-observability",
        "Grafana LGTM stack for local use (docker compose), the Alloy pipeline and the service dashboards.",
        "platform-demo-observability", "observability-stack", "observability",
        ["grafana/dashboard-selector: \"tags @> 'observability'\""], ["grafana", "otlp", "alloy"],
        [("Grafana", GRAFANA, "dashboard")],
        deps=["resource:default/grafana", "resource:default/alloy"])
    write_site(d, "platform-demo-observability", "platform-demo-observability",
               "Grafana LGTM stack, Alloy pipeline and service dashboards.", pages, nav, cat)


# ---------------------------------------------------------------------------------------------------------- org
def org() -> None:
    d = WORKSPACE / "platform/org-profile"
    prof = (d / "profile/README.md").read_text()
    body = prof.split("\n", 1)[1].strip()
    pages = {
        "index.md": f"""# platform-boutique

{hero("organisation", "An open-source platform-engineering project: an online shop built as the workload for a complete platform. Everything is public.")}
{cards([("Applications", "Eleven repositories named app-&lt;service&gt;.", "https://github.com/orgs/platform-boutique/repositories?q=props.category%3Aapp"),
        ("Deploy", "platform-demo-helm: charts, environments, GitOps, policies.", f"https://github.com/{ORG}/platform-demo-helm"),
        ("Platform", "Shared pipelines and the observability stack.", f"https://github.com/{ORG}/platform-demo-workflows"),
        ("Roadmap", "The public project board.", "https://github.com/orgs/platform-boutique/projects/1")])}
## The organisation front page

This is the README shown on <https://github.com/platform-boutique>, reproduced here so the portal explains the conventions too.

{body}
""",
    }
    cat = component("org-profile", "Organisation profile",
                    "The organisation's front page (the .github repository): the repository map and the conventions.",
                    ".github", "documentation", "developer-portal", [], ["documentation"], [])
    write_site(d, ".github", "platform-boutique", "The organisation's front page.", pages, [("Overview", "index.md")], cat)


if __name__ == "__main__":
    steps = {"helm": helm, "workflows": workflows, "docs": docs_repo, "observability": observability, "org": org}
    for name in (sys.argv[1:] or steps):
        steps[name]()
