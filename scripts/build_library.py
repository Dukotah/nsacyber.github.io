#!/usr/bin/env python3
"""Generate library.md and forks.md from the GitHub REST API.

Standard library only. A token is read from GH_TOKEN or GITHUB_TOKEN, or from
`gh auth token` if the GitHub CLI is installed; without one the unauthenticated
rate limit (60 requests/hour) applies, which is enough for a single run.

Usage: python3 scripts/build_library.py [--org nsacyber] [--fork-owner Dukotah]
"""

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTICE = ("This is an unofficial community fork of nsacyber.github.io. It is not affiliated with or "
          "endorsed by NSA. The generator and its output are in the fork's `lane/library-hub` branch.")


def token():
    for name in ("GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(name):
            return os.environ[name]
    if shutil.which("gh"):
        try:
            out = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=20)
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    return None


TOKEN = token()


def get(path, params=None, allow_404=False):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
               "User-Agent": "nsacyber-library-hub"}
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if allow_404 and e.code == 404:
            return None
        raise


def get_all(path, params=None):
    params = dict(params or {}, per_page=100)
    items, page = [], 1
    while True:
        batch = get(path, dict(params, page=page))
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1


def cell(text):
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def day(ts):
    return ts[:10] if ts else ""


def build_library(org):
    repos = [r for r in get_all("/orgs/%s/repos" % org, {"type": "public"}) if r["name"] != ".github"]
    active = sorted((r for r in repos if not r["archived"]), key=lambda r: r["pushed_at"] or "", reverse=True)
    archived = sorted((r for r in repos if r["archived"]), key=lambda r: r["pushed_at"] or "", reverse=True)
    lines = [
        "# nsacyber repositories",
        "",
        NOTICE,
        "",
        "Generated from the GitHub API on %s by `scripts/build_library.py`. "
        "%d public repositories in the [%s](https://github.com/%s) organization: %d not archived, %d archived. "
        "Sorted by last push, newest first." % (TODAY, len(repos), org, org, len(active), len(archived), ),
        "",
    ]
    for title, group in (("Not archived", active), ("Archived (read-only on GitHub)", archived)):
        lines += ["## %s" % title, "", "| Repository | Description | Language | Stars | Last push | License |",
                  "| --- | --- | --- | ---: | --- | --- |"]
        for r in group:
            lic = (r.get("license") or {}).get("spdx_id") or ""
            if lic == "NOASSERTION":
                lic = "other"
            lines.append("| [%s](%s) | %s | %s | %d | %s | %s |" % (
                r["name"], r["html_url"], cell(r["description"]), r["language"] or "",
                r["stargazers_count"], day(r["pushed_at"]), lic))
        lines.append("")
    data = [{k: r[k] for k in ("name", "html_url", "description", "language", "stargazers_count",
                               "pushed_at", "archived", "homepage")} for r in active + archived]
    return "\n".join(lines), data


def build_forks(owner, org):
    with open(os.path.join(ROOT, "data", "forks.json"), encoding="utf-8") as f:
        forks = json.load(f)
    lines = [
        "# Developed forks",
        "",
        NOTICE,
        "",
        "Forks of %s repositories under [%s](https://github.com/%s) with work on top. `fix/*` branches hold a "
        "small change shaped for an upstream pull request; `lane/*` branches hold fork-only extensions and a "
        "`LANE-REPORT.md` with the evidence. Nothing here has been merged upstream. Generated on %s; a fork "
        "is marked \"in progress\" until a `lane/*` branch with a `LANE-REPORT.md` exists." % (org, owner, owner, TODAY),
        "",
        "| Fork | Branches | Status | Summary |",
        "| --- | --- | --- | --- |",
    ]
    out = []
    for entry in forks:
        name = entry["repo"]
        fork = get("/repos/%s/%s" % (owner, name), allow_404=True)
        if fork is None:
            lines.append("| %s | | not found | |" % name)
            continue
        upstream = {b["name"] for b in get_all("/repos/%s/%s/branches" % (org, name))}
        mine = sorted(b["name"] for b in get_all("/repos/%s/%s/branches" % (owner, name))
                      if b["name"].startswith(("lane/", "fix/")) and b["name"] not in upstream)
        reported = [b for b in mine if b.startswith("lane/") and get(
            "/repos/%s/%s/contents/LANE-REPORT.md" % (owner, name), {"ref": b}, allow_404=True)]
        links = ", ".join("[`%s`](%s/tree/%s)" % (b, fork["html_url"], b) for b in mine) or "none pushed"
        if reported:
            status = "[report](%s/blob/%s/LANE-REPORT.md)" % (fork["html_url"], reported[0])
            summary = cell(entry.get("summary")) or "see report"
        else:
            status, summary = "in progress", ""
        lines.append("| [%s](%s) | %s | %s | %s |" % (name, fork["html_url"], links, status, summary))
        out.append({"repo": name, "fork": fork["html_url"], "branches": mine, "report_branch": (reported or [None])[0]})
    lines.append("")
    return "\n".join(lines), out


def write(rel, text):
    with open(os.path.join(ROOT, rel), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    global TODAY
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--org", default="nsacyber")
    ap.add_argument("--fork-owner", default="Dukotah")
    args = ap.parse_args()
    TODAY = datetime.date.today().isoformat()
    library, data = build_library(args.org)
    forks, fork_data = build_forks(args.fork_owner, args.org)
    write("library.md", library)
    write("forks.md", forks)
    write(os.path.join("data", "library.json"),
          json.dumps({"generated": TODAY, "repos": data, "forks": fork_data}, indent=2) + "\n")
    print("library.md: %d repos (%d archived); forks.md: %d forks, %d with a report" % (
        len(data), sum(r["archived"] for r in data), len(fork_data),
        sum(1 for f in fork_data if f["report_branch"])), file=sys.stderr)


TODAY = ""

if __name__ == "__main__":
    main()
