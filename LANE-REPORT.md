# LANE 10 report: nsacyber.github.io

Fork-only lane. Upstream is effectively closed: zero PRs have ever been merged, the last maintainer
commit was 2019-06-14 (iadgovuser1), and #9 (a 2023 URL refresh) was closed unmerged in 2025-04.
No PR or issue is drafted for opening upstream.

## 1. Upstream contribution rules

- CONTRIBUTING.md: non-government contributions are released under CC0 1.0; opening a PR is agreement
  to that waiver. No CLA, no DCO, no PR template, no CI, no tests.
- `scripts/` holds a PowerShell generator for `publications.md` that scrapes nsa.gov; it was not run.
- The tracker is spam: PRs #10-#14, #22-#30 ("Create SECURITY.md"), #31 (unrelated), issues #15-#20.

## 2. What changed and why

| Branch | Base | Commit(s) |
|---|---|---|
| `fix/dead-links` | upstream/master `a805bd6` | one commit: "Replace dead links on the open source page" (1 file, 8+/8-) |
| `lane/library-hub` | `fix/dead-links` | generator + pages + workflow + Pages config; this report |

### A: `fix/dead-links`
All 354 unique URLs in the Markdown pages were checked twice with a browser User-Agent (HEAD, then GET).
Only links that failed both runs with 404 or DNS failure were replaced, all in `opensource.md`:

| Old link | Result | Replacement | How found |
|---|---|---|---|
| `https://code.gov` | redirects to a digital.gov 404 | Wayback 2020-01-03 snapshot | Wayback availability API |
| `http://landhere.galois.com` | DNS failure | Wayback 2019-12-16 | Wayback |
| `https://babelfish.arc.nasa.gov/trac/jpf/wiki` | DNS failure | `https://github.com/javapathfinder/jpf-core/wiki` | jpf-core README: "All the latest developments ... can be found on our wiki" |
| `https://babelfish.arc.nasa.gov/trac/jpf/wiki/projects/jpf-mango` | DNS failure | Wayback 2016-08-01 | Wayback CDX |
| `https://github.com/OpenAttestation/OpenAttestation` | 404 | Wayback 2019-07-19 | Wayback |
| `https://01.org/openattestation` | redirects to Intel `404Redirector.aspx`, 403 | Wayback 2019-11-18 | Wayback |
| `https://bitbucket.org/seandroid` | 404 | Wayback 2021-10-27 | Wayback |
| `https://nsacyber.github.io/WALKOFF` | 404 (repo archived; Pages reports "built" from gh-pages but serves 404) | Wayback 2020-10-19 | Wayback |

Left alone, deliberately:
- **www.nsa.gov (33 links)**: inconclusive, not dead. The same URL returned 403 in one run and 200 in
  the other (e.g. `csa-bluekeep_20190604.pdf` redirected to `/portals/75/...` and served 200 in run 1,
  403 in run 2). Chrome on this network got an "Access Denied" page on `https://www.nsa.gov/` itself.
- `https://babelfish.arc.nasa.gov/hg/jpf/jpf-mango` (DNS failure) and `https://jpf.byu.edu/hg/jpf-mango`
  (connect timeout): no replacement exists. No Wayback capture of the hg repo, and no GitHub repo
  named jpf-mango (`gh search repos jpf-mango` returned nothing).
- `https://selinuxproject.org`: DNS resolves (207.210.245.134), connection refused. Not 404/DNS, so kept.
- `https://www.iad.gov`: untrusted certificate; the page cites it as "formerly", so kept.

### B: `lane/library-hub` (fork only)
- `scripts/build_library.py` (Python stdlib, token from `GH_TOKEN`/`GITHUB_TOKEN`/`gh auth token`):
  - `library.md`: every public nsacyber repo, with description, language, stars, last push and license,
    split into not-archived and archived.
  - `forks.md`: the 10 forks in this program. It lists `fix/*` and `lane/*` branches that exist on
    Dukotah but not upstream, and marks a fork "in progress" until a `lane/*` branch carries
    `LANE-REPORT.md`. One-line summaries live in `data/forks.json` and were written from each committed
    LANE-REPORT.md (all 10 lanes had pushed one by the time of writing except this one); they are only shown once a report exists.
  - `data/library.json`: the same data, machine-readable.
- `.github/workflows/library.yml`: on push to `lane/library-hub` it regenerates as a check. On the weekly
  cron or `workflow_dispatch` it regenerates and commits. Then lychee (`lychee.toml`) checks every `*.md`
  page and fails on any error. Exclusions are listed with reasons in `lychee.toml`: www.nsa.gov and the
  four known-dead links above.
- `_config.yml`: the title says "unofficial community fork". `index.md` adds the same notice and links to
  the two new pages. No NSA logos or branding were added.
- GitHub Pages is enabled on the fork only (legacy build from `lane/library-hub`, `/`).

## 3. Evidence

Link check, two runs (`check.py`, browser UA, 8 threads):
```
run1: 320 200, 23 403, 4 404, 7 ERR      run2: 309 200, 34 403, 4 404, 7 ERR
non-200 set identical except www.nsa.gov PDFs flipping between 200 and 403
```
Generator, local (WSL Python 3.14) and in Actions (3.12):
```
library.md: 39 repos (28 archived); forks.md: 10 forks, 6 with a report      # local
library.md: 39 repos (28 archived); forks.md: 10 forks, 7 with a report      # Actions, minutes later
library.md: 39 repos (28 archived); forks.md: 10 forks, 9 with a report      # local, before committing this report
```
Actions run 44248035058 (push, `Library`): regenerate OK, then lychee:
```
| Total 1320 | Successful 1249 | Timeouts 0 | Redirected 273 | Excluded 71 | Errors 0 |
```
Pages (`gh api -X POST repos/Dukotah/nsacyber.github.io/pages`), then `pages-build-deployment` success:
```
200 http://labs.copperbaytech.com/nsacyber.github.io/            (dukotah.github.io/nsacyber.github.io redirects here)
200 .../library.html   200 .../forks.html   200 .../opensource.html
```
The user site `dukotah.github.io` has the custom domain `labs.copperbaytech.com`, so every project page
on the account is served under that domain.

## 4. Competing work check

`gh pr list -R nsacyber/nsacyber.github.io --state all -L 50` at start and end. Authors: austinsteel,
lp6025095485-coder, lpaq76, sonoxo. None of the watched spray accounts appear.
- #9 "Outdated URL Updates" (austinsteel, closed unmerged 2025-04-11): changed `www.nsa.gov/what-we-do/cybersecurity/`
  to `www.nsa.gov/cybersecurity/` in README/publications. It does not overlap with A, which only touches non-nsa.gov links.
  https://github.com/nsacyber/nsacyber.github.io/pull/9
- Issue #1 "Outdated web page on iadgovadmin profile" (closed). No issue covers dead links.

## 5. Draft upstream text

None. Upstream has never merged a PR and the tracker is spam, so an issue would not be read. If the owner
wants one anyway, A's commit message is a complete PR body.

## 6. Land probability and next steps

- A upstream: **Low.** Nothing has merged in 7 years, and #9, the same kind of change, was closed unmerged.
- Owner next steps:
  1. The weekly cron does not fire yet. GitHub runs `schedule` only from the default branch, and the
     fork's `master` is kept as an upstream mirror. To get the weekly refresh, either make
     `lane/library-hub` the fork's default branch, or run "Library" manually (Actions tab > Library >
     Run workflow > branch `lane/library-hub`).
  2. A fork that joins the program later needs a line in `data/forks.json`; until its
     `lane/*` branch has a LANE-REPORT.md its row shows "in progress".
