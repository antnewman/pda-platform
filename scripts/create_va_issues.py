#!/usr/bin/env python3
"""Create GitHub Issues for the Verified Autonomy gap-closure backlog.

Reads `docs/verified-autonomy-backlog.yaml`. Idempotent: re-running with the
same manifest is safe. Each label/milestone/issue is created only if a match
is not already present.

Usage:
    python scripts/create_va_issues.py [--dry-run] [--repo OWNER/NAME]

Defaults to repo `antnewman/pda-platform`. Uses `gh` CLI for all GitHub
interactions, so the caller's existing `gh auth login` is the authority.

Outputs (when not in dry-run mode):
    - 1 milestone created (or matched)
    - up to 15 labels created (or matched)
    - 1 tracking issue (or matched by title)
    - 37 child issues (or matched by title)
    - `docs/verified-autonomy-backlog-created.md` summarising the run
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

# Ensure stdout/stderr emit UTF-8 on Windows consoles (em-dashes, arrows in titles).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

try:
    import yaml
except ImportError:  # pragma: no cover - human-readable hint
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# ─── small gh CLI wrappers ────────────────────────────────────────────────


def gh(*args: str, json_output: bool = False, check: bool = True) -> str:
    """Run `gh` with the given args. Return stdout as text."""
    cmd = ["gh", *args]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        sys.stderr.write(f"gh command failed: {' '.join(cmd)}\n{result.stderr}\n")
        sys.exit(result.returncode)
    return result.stdout


def gh_api(method: str, path: str, **fields: Any) -> dict:
    """Run `gh api -X METHOD path -f k=v ...` and return parsed JSON."""
    cmd = ["api", "-X", method, path]
    for key, value in fields.items():
        cmd.extend(["-f", f"{key}={value}"])
    out = gh(*cmd, json_output=True)
    return json.loads(out) if out.strip() else {}


# ─── label / milestone / issue helpers ────────────────────────────────────


def ensure_label(repo: str, name: str, color: str, description: str, dry_run: bool) -> None:
    """Create a label if it does not exist. Update colour/description if it does."""
    existing = gh("label", "list", "--repo", repo, "--json", "name,color,description",
                  "--limit", "200", check=False)
    try:
        labels = json.loads(existing) if existing.strip() else []
    except json.JSONDecodeError:
        labels = []
    match = next((l for l in labels if l["name"] == name), None)

    if match is None:
        action = f"CREATE label {name!r} (#{color})"
        if not dry_run:
            gh("label", "create", name, "--repo", repo, "--color", color,
               "--description", description)
        print(f"  [LABEL] {action}")
    else:
        # Match exists. Only re-edit if colour or description differs.
        if match.get("color", "").lower() != color.lower() or match.get("description", "") != description:
            action = f"UPDATE label {name!r}"
            if not dry_run:
                gh("label", "edit", name, "--repo", repo, "--color", color,
                   "--description", description)
            print(f"  [LABEL] {action}")
        else:
            print(f"  [LABEL] exists: {name!r}")


def ensure_milestone(repo: str, title: str, description: str, dry_run: bool) -> int:
    """Create a milestone if it does not exist. Return its number."""
    existing = gh("api", f"repos/{repo}/milestones?state=all", check=False)
    try:
        milestones = json.loads(existing)
    except json.JSONDecodeError:
        milestones = []
    match = next((m for m in milestones if m["title"] == title), None)

    if match is not None:
        print(f"  [MILESTONE] exists: {title!r} (#{match['number']})")
        return match["number"]

    if dry_run:
        print(f"  [MILESTONE] would CREATE: {title!r}")
        return -1

    created = gh_api("POST", f"repos/{repo}/milestones", title=title, description=description)
    print(f"  [MILESTONE] CREATED: {title!r} (#{created['number']})")
    return created["number"]


def find_issue_by_title(repo: str, title: str) -> dict | None:
    """Find an existing issue with the exact title (open or closed)."""
    out = gh("issue", "list", "--repo", repo, "--state", "all",
             "--limit", "200", "--search", f'in:title "{title}"',
             "--json", "number,title,state", check=False)
    try:
        issues = json.loads(out) if out.strip() else []
    except json.JSONDecodeError:
        return None
    return next((i for i in issues if i["title"] == title), None)


def create_issue(
    repo: str, title: str, body: str, labels: list[str],
    milestone_title: str | None, dry_run: bool,
) -> int:
    """Create an issue. Idempotent on title match.

    `gh issue create --milestone` accepts the milestone TITLE (not number),
    so we pass the title string through.
    """
    existing = find_issue_by_title(repo, title)
    if existing:
        print(f"  [ISSUE] exists: #{existing['number']} {title!r}")
        return existing["number"]

    if dry_run:
        print(f"  [ISSUE] would CREATE: {title!r}")
        return -1

    cmd = ["issue", "create", "--repo", repo, "--title", title, "--body", body]
    for label in labels:
        cmd.extend(["--label", label])
    if milestone_title:
        cmd.extend(["--milestone", milestone_title])

    out = gh(*cmd).strip()
    # gh prints the URL of the created issue on the last line.
    url = out.splitlines()[-1] if out else ""
    number = int(url.rsplit("/", 1)[-1]) if url else -1
    print(f"  [ISSUE] CREATED: #{number} {title!r}")
    return number


# ─── issue body composition ───────────────────────────────────────────────


CHILD_BODY_TEMPLATE = """**Layer:** {layer} — {layer_name}
**Type:** {kind}
**Paper reference:** {paper_section}
**Evidence tier:** {evidence_tier}
**Branch:** `{branch}`

## Scope

{scope}

## Acceptance criteria

- [ ] Code change scoped to the file(s) listed in the plan
- [ ] One regression test class added to `test_pda_platform.py`
- [ ] All existing tests still pass locally
- [ ] PR description includes `Closes #{this_issue}` (auto-closes on merge)
- [ ] For integrations: live MCP smoke test passes against Render after `dev → main` promotion

## Depends on

{depends_on_text}

## Source

Plan: `~/.claude/plans/serene-sleeping-globe.md` · Report: `PDA-platform-gap-analysis-verified-autonomy.docx` · Paper: [10.5281/zenodo.19096229](https://doi.org/10.5281/zenodo.19096229)
"""

LAYER_NAMES = {
    1: "Inverse Confidence Weighting",
    2: "Outlier Detection as Hard Escalation",
    3: "Making Failures Visible",
    4: "Calibration and Conformal Prediction",
    5: "Deterministic Guardrails",
    6: "RAG as Explainability",
    7: "Adversarial Testing",
    8: "Cryptographic Audit Trails",
    9: "Formal Verification",
}


def render_child_body(
    item: dict, kind: str, this_issue_number: int | str,
    issue_numbers: dict[str, int],
) -> str:
    """Render a child issue's body. `kind` is 'Foundation' or 'Integration'."""
    scope = item.get("scope")
    if scope is None:
        # Integration items use either a templated scope from tool/module or custom_body
        if "custom_body" in item:
            scope = item["custom_body"]
        elif "tool" in item:
            scope = (
                f"Wire `{item['tool']}` in `{item['module']}` through the "
                f"foundation from this layer's Phase 2 PR. Define the per-tool "
                f"policy (forbidden phrases, required fields, output constraints), "
                f"apply the wrapper, record audit-trail entries. "
                f"\n\n"
                + (item.get("note") and f"Note: {item['note']}\n" or "")
            )
        elif "decisions" in item:
            scope = (
                f"Wire the `{item['module']}` module's decision-producing "
                f"handlers through the generic audit chain from A1. "
                f"Decisions to chain: {item['decisions']}."
            )
        else:
            scope = "(See plan file for scope details.)"

    deps = item.get("depends_on", [])
    if not deps:
        depends_text = "None."
    else:
        lines = []
        for dep_id in deps:
            num = issue_numbers.get(dep_id)
            if num and num > 0:
                lines.append(f"- {dep_id}: #{num}")
            else:
                lines.append(f"- {dep_id} (issue number TBD)")
        depends_text = "\n".join(lines)

    return CHILD_BODY_TEMPLATE.format(
        layer=item["layer"],
        layer_name=LAYER_NAMES[item["layer"]],
        kind=kind,
        paper_section=item.get("paper_section", "n/a"),
        evidence_tier=item.get("evidence_tier", "(see plan)"),
        branch=item.get("branch", "n/a"),
        scope=scope.strip(),
        depends_on_text=depends_text,
        this_issue=this_issue_number,
    )


# ─── main flow ────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="antnewman/pda-platform",
                        help="OWNER/NAME of the target repo (default: antnewman/pda-platform)")
    parser.add_argument("--manifest", default="docs/verified-autonomy-backlog.yaml",
                        help="Path to the manifest YAML")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would happen; create nothing")
    parser.add_argument("--summary-out", default="docs/verified-autonomy-backlog-created.md",
                        help="Where to write the created-issue summary")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))

    print(f"=== Verified Autonomy backlog creation {'(DRY RUN)' if args.dry_run else ''} ===")
    print(f"Target repo: {args.repo}")
    print(f"Manifest:    {manifest_path}")
    print()

    # 1. Labels
    print("Labels:")
    for label in manifest["labels"]:
        ensure_label(args.repo, label["name"], label["color"],
                     label.get("description", ""), args.dry_run)

    # 2. Milestone
    print("\nMilestone:")
    ms = manifest["milestone"]
    milestone_number = ensure_milestone(args.repo, ms["title"], ms["description"], args.dry_run)
    milestone_title = ms["title"]

    # 3. Tracking issue
    print("\nTracking issue:")
    tracking = manifest["tracking_issue"]
    tracking_labels = ["verified-autonomy"] + tracking.get("extra_labels", [])
    tracking_number = create_issue(
        args.repo, tracking["title"], tracking["body"],
        tracking_labels, milestone_title, args.dry_run,
    )

    # 4. Foundation + integration issues
    issue_numbers: dict[str, int] = {}

    print("\nFoundation issues:")
    for item in manifest["foundations"]:
        labels = [
            "verified-autonomy",
            f"layer-{item['layer']}",
            "foundation",
            item.get("evidence_tier_label", "evidence-tier-strongest"),
        ]
        body = render_child_body(item, "Foundation", "TBD", issue_numbers)
        number = create_issue(
            args.repo, item["title"], body, labels,
            milestone_title, args.dry_run,
        )
        issue_numbers[item["id"]] = number

    print("\nIntegration issues:")
    for item in manifest["integrations"]:
        labels = [
            "verified-autonomy",
            f"layer-{item['layer']}",
            "integration",
            item.get("evidence_tier_label", "evidence-tier-strongest"),
        ]
        body = render_child_body(item, "Integration", "TBD", issue_numbers)
        number = create_issue(
            args.repo, item["title"], body, labels,
            milestone_title, args.dry_run,
        )
        issue_numbers[item["id"]] = number

    # 5. Update tracking issue body with task list
    if not args.dry_run and tracking_number > 0:
        tasks = []
        tasks.append("\n### Phase 2 — Foundations")
        for item in manifest["foundations"]:
            num = issue_numbers.get(item["id"])
            if num and num > 0:
                tasks.append(f"- [ ] {item['id']} · #{num} · {item['title']}")
        tasks.append("\n### Phase 3 — Integrations")
        for item in manifest["integrations"]:
            num = issue_numbers.get(item["id"])
            if num and num > 0:
                tasks.append(f"- [ ] {item['id']} · #{num} · {item['title']}")

        updated_body = tracking["body"] + "\n\n" + "\n".join(tasks)
        print(f"\nUpdating tracking issue #{tracking_number} with task list ...")
        gh("issue", "edit", str(tracking_number), "--repo", args.repo, "--body", updated_body)
        print(f"  [TRACKING] task list appended ({len(issue_numbers)} children)")

    # 6. Summary file
    if not args.dry_run:
        summary_lines = [
            "# Verified Autonomy backlog — created issues",
            "",
            f"Repository: `{args.repo}`",
            f"Milestone: #{milestone_number} — {ms['title']}",
            f"Tracking issue: #{tracking_number}",
            "",
            "| ID | Issue | Type | Layer | Title |",
            "|----|-------|------|-------|-------|",
        ]
        for item in manifest["foundations"]:
            num = issue_numbers.get(item["id"])
            summary_lines.append(f"| {item['id']} | #{num} | Foundation | L{item['layer']} | {item['title']} |")
        for item in manifest["integrations"]:
            num = issue_numbers.get(item["id"])
            summary_lines.append(f"| {item['id']} | #{num} | Integration | L{item['layer']} | {item['title']} |")

        Path(args.summary_out).write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
        print(f"\nSummary written to {args.summary_out}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
