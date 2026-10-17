#!/usr/bin/env python3
"""Scaffold the catalog descriptor and the TechDocs site of every repository of the organisation.

What it writes into each repository (working tree only, nothing is committed or pushed):

    catalog-info.yaml          the Backstage descriptor (Component/API entities, annotations the plugins read)
    mkdocs.yml                 the TechDocs site definition (navigation, shared Material settings)
    docs/index.md ...          the pages, split out of the repository's README so nothing has to be written twice

It is a scaffold, not a build step: after the first run the files are the source of truth and are edited by hand.
Running it again overwrites generated pages, so do that only on a clean branch and review the diff.

    python3 tools/techdocs/scaffold.py            # every repository
    python3 tools/techdocs/scaffold.py ad-service # one
"""
from __future__ import annotations

import re
import shutil
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = Path(__file__).resolve().parents[4]  # ~/Desktop/platform-demo
ORG = "platform-boutique"
GRAFANA = "https://grafana.platform-demo.test"
ARGOCD = "https://argocd.platform-demo.test"


@dataclass
class Svc:
    name: str  # catalog name == Kubernetes app name == folder under apps/
    repo: str  # GitHub repository name
    lang: str
    runtime: str
    port: str
    proto: str | None  # path of the .proto file inside the repository
    calls: list[str] = field(default_factory=list)  # components this one depends on
    tags: list[str] = field(default_factory=list)
    dashboard_tag: str | None = None
    folder: str = ""
    kind: str = "service"
    resources: list[str] = field(default_factory=list)  # catalog Resources it depends on


SERVICES = [
    Svc("frontend", "app-frontend", "Go", "Go 1.25", "8080 (HTTP)", None,
        ["ad-service", "cart-service", "checkout-service", "currency-service", "product-catalog-service",
         "recommendation-service", "shipping-service"], ["go", "http"], "frontend", kind="website"),
    Svc("ad-service", "app-ad-service", "Java", "Java 21", "9555 (gRPC)", "src/main/proto/ad.proto", [],
        ["java", "grpc"], "ad"),
    Svc("cart-service", "app-cart-service", ".NET", ".NET 10", "7070 (gRPC)", "src/protos/cart.proto", [],
        ["dotnet", "grpc"], "cart", resources=["cart-redis"]),
    Svc("checkout-service", "app-checkout-service", "Go", "Go 1.25", "5050 (gRPC)", "proto/checkout.proto",
        ["cart-service", "currency-service", "email-service", "payment-service", "product-catalog-service",
         "shipping-service"], ["go", "grpc"], "checkout"),
    Svc("currency-service", "app-currency-service", "TypeScript", "Node 22", "7000 (gRPC)", "proto/currency.proto", [],
        ["nodejs", "typescript", "grpc"], "currency"),
    Svc("email-service", "app-email-service", "Python", "Python 3.12", "8080 (gRPC)", "proto/email.proto", [],
        ["python", "grpc"], "email"),
    Svc("payment-service", "app-payment-service", "TypeScript", "Node 22", "50051 (gRPC)", "proto/payment.proto", [],
        ["nodejs", "typescript", "grpc"], "payment"),
    Svc("product-catalog-service", "app-product-catalog-service", "Go", "Go 1.25", "3550 (gRPC)",
        "proto/productcatalog.proto", ["product-catalog-db"], ["go", "grpc"], "product-catalog"),
    Svc("recommendation-service", "app-recommendation-service", "Python", "Python 3.12", "8080 (gRPC)",
        "proto/recommendation.proto", ["product-catalog-service"], ["python", "grpc"], "recommendation"),
    Svc("shipping-service", "app-shipping-service", "Go", "Go 1.25", "50051 (gRPC)", "proto/shipping.proto", [],
        ["go", "grpc"], "shipping"),
    Svc("product-catalog-db", "app-product-catalog-db", "SQL", "PostgreSQL 17", "5432 (SQL)", None, [],
        ["postgresql", "database"], None, kind="database"),
]
for s in SERVICES:
    s.folder = f"apps/{s.name if s.name != 'frontend' else 'frontend'}"

CALLED_BY: dict[str, list[str]] = {s.name: [] for s in SERVICES}
for s in SERVICES:
    for c in s.calls:
        CALLED_BY.setdefault(c, []).append(s.name)


# ------------------------------------------------------------------------------------------------ README splitting
def read_sections(readme: Path) -> tuple[str, str, dict[str, str]]:
    """Return (title, lead paragraph(s), {heading: body}) of a README, keeping `##` sections in order."""
    text = readme.read_text()
    lines = text.splitlines()
    title = next((l[2:].strip() for l in lines if l.startswith("# ")), readme.parent.name)
    out: dict[str, list[str]] = {}
    lead: list[str] = []
    cur: str | None = None
    in_code = False
    for line in lines:
        if line.startswith("```"):
            in_code = not in_code
        if not in_code and line.startswith("## "):
            cur = line[3:].strip()
            out[cur] = []
            continue
        if cur is None:
            if not line.startswith("# "):
                lead.append(line)
        else:
            out[cur].append(line)
    return title, "\n".join(lead).strip(), {k: "\n".join(v).strip("\n") for k, v in out.items()}


def github_url(repo: str, path: str) -> str:
    path = path.lstrip("./")
    kind = "tree" if path.endswith("/") or "." not in Path(path).name else "blob"
    return f"https://github.com/{ORG}/{repo}/{kind}/main/{path}"


def fix_links(md: str, repo: str, page_of_anchor: dict[str, tuple[str, str]], current: str) -> str:
    """Relative links in a README point at repository files; in the docs site they must point at GitHub."""

    def repl(m: re.Match) -> str:
        label, target = m.group(1), m.group(2)
        if re.match(r"^(https?:|mailto:)", target):
            return m.group(0)
        if target.startswith("#"):
            hit = page_of_anchor.get(target[1:])
            if hit:
                page, anchor = hit
                return f"[{label}]({'' if page == current else page}#{anchor})"
            return m.group(0)
        if target.startswith("../"):
            # a sibling folder of the workspace: apps/<service> is the repository app-<service>
            name = target[3:].strip("/").split("/")[0]
            return f"[{label}](https://github.com/{ORG}/app-{name})" if name else m.group(0)
        if "platform-demo root" in label:
            return m.group(0)
        return f"[{label}]({github_url(repo, target)})"

    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", repl, md)


def slug(heading: str) -> str:
    """GitHub's anchor for a heading (README links are written for GitHub): every space becomes a hyphen."""
    s = re.sub(r"[^\w\- ]", "", heading.lower()).strip()
    return s.replace(" ", "-")


def mk_slug(heading: str) -> str:
    """Python-Markdown's anchor (what the TechDocs page uses): runs of spaces and hyphens collapse into one hyphen."""
    s = re.sub(r"[^\w\- ]", "", heading.lower()).strip()
    return re.sub(r"[-\s]+", "-", s)


PAGE_ORDER = [
    ("index.md", "Overview", ["At a glance"]),
    ("api.md", "API", ["API", "HTTP routes", "What's inside"]),
    ("configuration.md", "Configuration", ["Configuration"]),
    ("container-image.md", "Container image", ["Container image"]),
    ("kubernetes.md", "Kubernetes", ["Kubernetes deployment notes"]),
    ("observability.md", "Observability", ["Observability"]),
    ("development.md", "Develop & test", ["Running locally", "Project structure"]),
    ("limitations.md", "Known limitations", ["Known limitations"]),
]

ICON = {  # tiny inline marks used in page headers (CSS only, no external assets)
    "index.md": "",
}


def mermaid_neighbourhood(s: Svc) -> str:
    callers = CALLED_BY.get(s.name, [])
    lines = ["```mermaid", "flowchart LR"]
    me = f'{node(s.name)}["<b>{s.name}</b><br/>{s.port}"]:::me'
    lines.append(f"  {me}")
    for c in callers:
        lines.append(f'  {node(c)}["{c}"] --> {node(s.name)}')
    for c in s.calls:
        lines.append(f'  {node(s.name)} --> {node(c)}["{c}"]')
    for r in s.resources:
        lines.append(f'  {node(s.name)} --> {node(r)}[("{r}")]')
    if not callers and s.name == "frontend":
        lines.append('  browser(["Browser"]) --> ' + node(s.name))
    lines.append("  classDef me stroke-width:3px;")
    lines.append("```")
    return "\n".join(lines)


def node(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "_", name)


def service_pages(s: Svc, repo_dir: Path) -> dict[str, str]:
    title, lead, sections = read_sections(repo_dir / "README.md")
    # which page does each heading end up on
    page_of_anchor: dict[str, tuple[str, str]] = {}
    page_sections: dict[str, list[tuple[str, str]]] = {}
    for page, _t, heads in PAGE_ORDER:
        for h in heads:
            if h in sections:
                page_of_anchor[slug(h)] = (page, mk_slug(h))
                page_sections.setdefault(page, []).append((h, sections[h]))
    placed = {h for p in page_sections.values() for h, _ in p}
    # sections no page claims are appended to the API page so nothing from the README is lost
    for h, body in sections.items():
        if h not in placed:
            page_of_anchor[slug(h)] = ("api.md", mk_slug(h))
            page_sections.setdefault("api.md", []).append((h, body))

    pages: dict[str, str] = {}
    for page, ptitle, _heads in PAGE_ORDER:
        if page == "index.md":
            continue
        secs = page_sections.get(page)
        if not secs:
            continue
        body = []
        for h, text in secs:
            body.append(f"## {h}\n\n{text}\n")
        md = f"# {ptitle}\n\n" + "\n".join(body)
        # a page with a single `##` section does not need the section heading repeated under the page title
        if len(secs) == 1:
            md = f"# {ptitle}\n\n{secs[0][1]}\n"
        pages[page] = fix_links(md, s.repo, page_of_anchor, page)

    # ---- overview
    glance = sections.get("At a glance", "")
    called_by = ", ".join(f"`{c}`" for c in CALLED_BY.get(s.name, [])) or "no other service"
    calls = ", ".join(f"`{c}`" for c in s.calls + s.resources) or "nothing (leaf service)"
    state = "Stateless" if s.kind != "database" else "Stateful"
    index = f"""# {s.name}

<div class="pd-hero" markdown>
<span class="pd-kicker">{s.kind} · platform-demo</span>

{lead.split(chr(10) + chr(10))[0]}
</div>

<div class="pd-facts" markdown>
<div><span>Runtime</span><strong>{s.runtime}</strong><small>{s.lang}</small></div>
<div><span>Listens on</span><strong>{s.port.split(' ')[0]}</strong><small>{s.port.split(' ', 1)[1].strip('()') if ' ' in s.port else ''}</small></div>
<div><span>State</span><strong>{state}</strong></div>
<div><span>Image</span><strong>{s.repo.replace('app-', '')}</strong><small>mladenovskistefan/</small></div>
</div>

## Where it sits

{called_by_sentence(s)}

{mermaid_neighbourhood(s)}

## At a glance

{fix_links(glance, s.repo, page_of_anchor, 'index.md')}

## Find it elsewhere

<div class="pd-cards" markdown>
<div><h4><a href="{ARGOCD}/applications/argocd/dev-{s.name}">Argo CD</a></h4><p>Sync and health of <code>dev-{s.name}</code>.</p></div>
{grafana_card(s)}
<div><h4><a href="https://github.com/{ORG}/{s.repo}">Repository</a></h4><p>Source, pull requests and releases of <code>{s.repo}</code>.</p></div>
</div>

!!! info "Part of the platform-demo platform"
    Cross-cutting facts (service wiring, observability contract, Kubernetes translation, CI/CD) are in the
    [master reference](https://github.com/{ORG}/platform-demo-docs). This site only describes {s.name}.
"""
    pages["index.md"] = index
    return pages


def called_by_sentence(s: Svc) -> str:
    cb = CALLED_BY.get(s.name, [])
    parts = []
    if s.name == "frontend":
        parts.append("Browsers talk to the storefront only; it fans out to the backends below.")
    elif cb:
        parts.append("Called by " + ", ".join(f"`{c}`" for c in cb) + ".")
    else:
        parts.append("Nothing calls this service directly.")
    if s.calls or s.resources:
        parts.append("It calls " + ", ".join(f"`{c}`" for c in s.calls + s.resources) + ".")
    else:
        parts.append("It has no downstream dependencies.")
    return " ".join(parts)


def grafana_card(s: Svc) -> str:
    if not s.dashboard_tag:
        return ""
    uid = {
        "product-catalog": "product-catalog-overview",
        "frontend": "frontend-overview",
    }.get(s.dashboard_tag, f"{s.dashboard_tag}-service-overview")
    return (f'<div><h4><a href="{GRAFANA}/d/{uid}">Grafana</a></h4><p>Latency, traffic and errors '
            f'(<code>{uid}</code>).</p></div>')


def mkdocs_yml(s_name: str, site_name: str, description: str, nav: list[tuple[str, str]], repo: str,
               extra_md: list[str] | None = None) -> str:
    nav_lines = "\n".join(f"  - {yq(t)}: {p}" for t, p in nav)
    return f"""# TechDocs site (https://backstage.io/docs/features/techdocs/). Built by the portal's backend with mkdocs-techdocs-core;
# the theme and extensions come from there, the look from docs/stylesheets/extra.css (shared by all repositories).
site_name: {yq(site_name)}
site_description: {yq(description)}
repo_url: https://github.com/{ORG}/{repo}
edit_uri: edit/main/docs/

plugins:
  - techdocs-core

theme:
  name: material
  features:
    - navigation.sections
    - navigation.top
    - content.code.copy

nav:
{nav_lines}
"""


def yq(s: str) -> str:
    return '"' + s.replace('"', '\\"') + '"'


def catalog_info(s: Svc, description: str) -> str:
    consumes = [f"{c}-api" for c in s.calls if c not in ("product-catalog-db",)]
    api_block = ""
    provides = ""
    if s.proto:
        api_block = f"""---
apiVersion: backstage.io/v1alpha1
kind: API
metadata:
  name: {s.name}-api
  description: gRPC interface of {s.name} (Protocol Buffers).
  tags: [grpc, protobuf]
  links:
    - {{ url: "https://github.com/{ORG}/{s.repo}/blob/main/{s.proto}", title: "{Path(s.proto).name} on GitHub", icon: code }}
spec:
  type: grpc
  lifecycle: experimental
  owner: group:default/maintainers
  system: shop
  definition:
    $text: ./{s.proto}
"""
        provides = f"  providesApis: [{s.name}-api]\n"
    dep_lines = [f"    - component:default/{c}" for c in s.calls]
    dep_lines += [f"    - resource:default/{r}" for r in s.resources]
    deps = ("  dependsOn:\n" + "\n".join(dep_lines) + "\n") if dep_lines else ""
    cons = f"  consumesApis: [{', '.join(consumes)}]\n" if consumes else ""
    links = [
        f'    - {{ url: "https://github.com/{ORG}/{s.repo}", title: Repository, icon: github }}',
    ]
    ann = [
        f"    github.com/project-slug: {ORG}/{s.repo}",
        "    backstage.io/techdocs-ref: dir:.",
    ]
    if s.name != "product-catalog-db":
        ann += [
            f"    backstage.io/kubernetes-id: {s.name}",
            "    backstage.io/kubernetes-namespace: platform-demo",
            f"    backstage.io/kubernetes-label-selector: app.kubernetes.io/name={s.name}",
            f"    argocd/app-name: dev-{s.name}",
        ]
        links.append(f'    - {{ url: "{ARGOCD}/applications/argocd/dev-{s.name}", title: Argo CD, icon: dashboard }}')
    else:
        ann += [
            "    backstage.io/kubernetes-id: product-catalog-db",
            "    backstage.io/kubernetes-namespace: platform-demo",
            "    backstage.io/kubernetes-label-selector: app.kubernetes.io/name=product-catalog-db",
            "    argocd/app-name: dev-product-catalog-db",
        ]
        links.append(f'    - {{ url: "{ARGOCD}/applications/argocd/dev-product-catalog-db", title: Argo CD, icon: dashboard }}')
    if s.dashboard_tag:
        uid = {"product-catalog": "product-catalog-overview", "frontend": "frontend-overview"}.get(
            s.dashboard_tag, f"{s.dashboard_tag}-service-overview")
        ann += [
            f"    grafana/dashboard-selector: \"tags @> '{s.dashboard_tag}'\"",
            f"    grafana/alert-label-selector: \"service={s.name}\"",
            f"    grafana/overview-dashboard: \"{GRAFANA}/d/{uid}\"",
        ]
        links.append(f'    - {{ url: "{GRAFANA}/d/{uid}", title: Grafana dashboard, icon: dashboard }}')
    ctype = {"service": "service", "website": "website", "database": "database"}[s.kind]
    return f"""apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: {s.name}
  title: {s.name}
  description: {yq(description)}
  annotations:
{chr(10).join(ann)}
  tags: [{', '.join(s.tags)}]
  links:
{chr(10).join(links)}
spec:
  type: {ctype}
  lifecycle: experimental
  owner: group:default/maintainers
  system: shop
{provides}{cons}{deps.rstrip(chr(10))}
{api_block}""".replace("\n\n---", "\n---").rstrip() + "\n"


def one_line(lead: str) -> str:
    first = lead.split("\n\n")[0].replace("\n", " ")
    first = re.sub(r"`([^`]+)`", r"\1", first)
    first = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", first)
    m = re.match(r"(.+?[.!?])(\s|$)", first)
    return (m.group(1) if m else first).strip()


def write_service(s: Svc) -> None:
    repo_dir = WORKSPACE / s.folder
    if not repo_dir.is_dir():
        print(f"skip {s.name}: {repo_dir} missing")
        return
    title, lead, _ = read_sections(repo_dir / "README.md")
    pages = service_pages(s, repo_dir)
    docs = repo_dir / "docs"
    docs.mkdir(exist_ok=True)
    nav = []
    for page, ptitle, _ in PAGE_ORDER:
        if page in pages:
            (docs / page).write_text(pages[page])
            nav.append((ptitle, page))
    desc = one_line(lead)
    (repo_dir / "mkdocs.yml").write_text(mkdocs_yml(s.name, s.name, desc, nav, s.repo))
    (repo_dir / "catalog-info.yaml").write_text(catalog_info(s, desc))
    print(f"{s.name}: {len(pages)} pages")


if __name__ == "__main__":
    only = set(sys.argv[1:])
    for svc in SERVICES:
        if not only or svc.name in only:
            write_service(svc)
