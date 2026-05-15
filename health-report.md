# n8n-mcp-python health check — 2026-05-15 UTC

## Verdict

**needs attention — v0.1.0 tag not created; package unpublished to PyPI; CI run history unavailable via current tooling**

---

## CI

> **Note:** The `gh` CLI is not installed in this environment and no GitHub Actions run-history MCP tool is available. CI run results below are inferred from commit history and workflow configuration. Direct run links cannot be provided.

| Branch | Status | Latest Push | Notes |
|--------|--------|-------------|-------|
| `master` | ⚠️ Unknown (no API access) | 2026-05-01 | Last commit: merge of PR #8 (Phases 0–6 release) |
| `develop` | — | *(branch deleted)* | Merged into master via PR #8; branch no longer exists |

### Workflow triggers (from `ci.yml`)
- Runs on **push** and **pull_request** to `master` or `develop`
- Matrix: Python **3.11** and **3.12**
- Steps: `ruff check src tests` → `pytest -q`

⚠️ **Dead trigger**: `ci.yml` still lists `develop` as a branch trigger, but that branch was deleted on 2026-05-01. This is harmless but may cause confusion.

---

## Workflows

| Workflow | File | Trigger | State |
|----------|------|---------|-------|
| CI | `.github/workflows/ci.yml` | push/PR to master or develop | ✅ active |
| Publish to PyPI | `.github/workflows/publish.yml` | push of `v*` tag or manual dispatch | ✅ active (never triggered — no `v*` tag exists) |

---

## Branches

Only **one** remote branch exists: `master`.

No `feature/*` or `fix/*` branches are present. The `develop` branch and all feature/fix branches (phases 1–6 + `fix/scrub-example-workflow-id`) were deleted after merging on 2026-05-01.

**Stale branches: none.**

---

## Security

| Source | Result |
|--------|--------|
| GitHub Advanced Security / Secret Scanning | ❌ Not enabled on this repo |
| GitHub Code Scanning | ❌ Not enabled |
| Dependabot alerts | ⚠️ Could not retrieve (no `gh` CLI, no Dependabot MCP tool) |
| Manual grep of `src/` for hardcoded secrets | ✅ Clean — no tokens, passwords, or API keys found |

### ⚠️ Outstanding action item (from PR #8 description)

> "Rotate the n8n public-API JWT used during development — it was in **chat transcripts** during the build session."

This was flagged by the repo owner in the PR #8 body. The JWT itself was never committed to the repository (the post-merge audit confirmed no tokens in tracked files or git history), but if it was used in external chat sessions (e.g. Claude conversations), the token should be rotated now if not already done.

### Dependency risk (estimated)

`pyproject.toml` declares these production dependencies with loose version pins:

| Package | Pin | Risk |
|---------|-----|------|
| `mcp` | `>=1.0.0` | Medium — fast-moving SDK; no upper bound |
| `httpx` | `>=0.27.0` | Low |
| `pydantic` | `>=2.5.0` | Low |
| `python-dotenv` | `>=1.0.0` | Low |

Enabling GitHub Dependabot would surface any CVEs automatically.

---

## Activity

### Open pull requests
*None.* All 8 PRs are closed/merged.

### Recently merged pull requests (all on 2026-05-01)

| # | Title | Merged |
|---|-------|--------|
| #8 | Release: develop → master (Phases 0–6, full v0.1.0 surface) | 2026-05-01 |
| #7 | fix: scrub real workflow id from docstring example | 2026-05-01 |
| #6 | Phase 6: packaging, CI, install docs | 2026-05-01 |
| #5 | Phase 5: enterprise endpoints | 2026-05-01 |
| #4 | Phase 4: tags, credentials, variables CRUD | 2026-05-01 |
| #3 | Phase 3: execution tools | 2026-05-01 |
| #2 | Phase 2: workflow mutations | 2026-05-01 |
| #1 | Phase 1: read-only workflow tools | 2026-05-01 |

### Open issues
*None.*

### Latest 5 commits on `master` (no separate `develop` branch)

| SHA | Author | When | Message |
|-----|--------|------|---------|
| `8f1298f` | CKSoupen | 2026-05-01 | Merge PR #8 — Release: develop → master |
| `9bc7550` | CKSoupen | 2026-05-01 | Merge PR #7 — fix: scrub real workflow id |
| `0367e5a` | CKSoupen | 2026-05-01 | Replace real example workflow id in docstring |
| `24cd724` | CKSoupen | 2026-05-01 | Merge PR #6 — Phase 6: packaging, CI, install docs |
| `df4cadc` | CKSoupen | 2026-05-01 | Phase 6: packaging, GitHub Actions, install docs |

**Repository activity note**: All 8 PRs and all commits landed on a single day (2026-05-01, ~14 days ago). The repo has been idle since then. There are 40 tools implemented, 60/60 unit tests passing at time of last commit, ruff-clean.

---

## Recommended actions

Ordered by priority:

1. **[HIGH] Create the `v0.1.0` git tag to publish to PyPI.**
   The `pyproject.toml` already declares `version = "0.1.0"` and the `publish.yml` workflow is wired to fire on any `v*` tag push. Before tagging:
   - Confirm PyPI **Trusted Publishing** is configured in your PyPI project settings for this repo (required for the `pypa/gh-action-pypi-publish` action to work without a token).
   - Then: `git tag v0.1.0 && git push origin v0.1.0`

2. **[HIGH] Rotate the n8n API key used during development.**
   PR #8 explicitly notes the development JWT appeared in external chat transcripts. Rotate it in your n8n instance's API settings if not already done.

3. **[MEDIUM] Enable GitHub Dependabot.**
   Go to *Settings → Security → Dependabot* and enable dependency alerts + security updates. The repo has four production dependencies with unbounded version pins.

4. **[MEDIUM] Fix the dead `develop` branch trigger in `ci.yml`.**
   The `develop` branch was deleted on 2026-05-01. Update `ci.yml` to remove it (or replace it with a wildcard like `feature/**`) so the workflow config reflects reality.

5. **[LOW] Enable GitHub Advanced Security / Secret Scanning.**
   Currently not enabled. This would automatically catch any future accidental credential commits.

6. **[LOW] Verify CI actually passed on the final `master` push.**
   CI run history could not be retrieved in this session. Confirm the CI check on commit `8f1298f` is green via the GitHub Actions tab.

7. **[LOW] Consider adding `CONTRIBUTING.md`.**
   Noted as a future task in PR #6. Now that the package is ready for public consumption, a contributing guide helps external contributors.

---

*Report generated: 2026-05-15 UTC | Agent: Claude Code health-check | Repo: github.com/CKSoupen/n8n-mcp-python*
