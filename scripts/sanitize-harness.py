#!/usr/bin/env python3
"""Generate a publishable, templated copy of the live Claude Code harness.

Reads the whitelist and rules in harness-scrub.toml, pulls each listed file out
of ~/.claude (plus ~/.zshrc and ~/Library/LaunchAgents), rewrites employer- and
identity-specific strings into {{placeholders}}, and writes the result to
harness/ in this repo.

The output is what ships publicly. The live ~/.claude is never modified.

Design notes:

- **Whitelist, never blacklist.** ~/.claude also holds session transcripts,
  telemetry, and caches containing work conversation content. Only files named
  explicitly in the TOML are ever read.
- **Reproducible.** No timestamps, no ordering nondeterminism. Running twice
  produces a byte-identical tree, which is what makes the round-trip check in
  REBUILD.md meaningful.
- **Fails closed.** If a forbidden pattern survives into the output, the run
  exits non-zero and the tree is left for inspection. New secrets appearing in
  ~/.claude later will trip this rather than being published silently.

Usage:
    python3 scripts/sanitize-harness.py [--check]

    --check   Generate into a temp dir and diff against the committed harness/.
              Exits non-zero if they differ. For the round-trip verification.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = Path(__file__).resolve().parent / "harness-scrub.toml"

# Sentinel wrapper for protected strings. Chosen to be something that cannot
# occur in the source files and that no substitution pattern can match.
_SENTINEL = "\x00PROTECT{}\x00"


class ScrubError(Exception):
    """A forbidden pattern survived into the generated output."""


def load_rules() -> dict:
    with RULES_PATH.open("rb") as fh:
        rules = tomllib.load(fh)

    # A bare `protect = [...]` written below the [meta] header is parsed as
    # meta.protect and would be silently ignored, letting every protected
    # string get substituted anyway. Fail loudly instead.
    if "protect" in rules.get("meta", {}):
        raise ScrubError(
            "`protect` is nested under [meta] — move it above the first "
            "[table] header in harness-scrub.toml so it parses as top-level."
        )

    return rules


def expand(path_str: str, source_root: Path) -> Path:
    """Resolve a TOML `src` to an absolute path.

    Entries starting with ~ are user-absolute (e.g. ~/.zshrc); everything else
    is relative to the harness source root (~/.claude).
    """
    if path_str.startswith("~"):
        return Path(path_str).expanduser()
    return source_root / path_str


def apply_substitutions(text: str, rules: dict) -> str:
    """protect -> substitute -> restore."""
    protected = rules.get("protect", [])

    for i, literal in enumerate(protected):
        text = text.replace(literal, _SENTINEL.format(i))

    for rule in rules.get("substitutions", []):
        text = re.sub(rule["pattern"], rule["replacement"], text)

    for i, literal in enumerate(protected):
        text = text.replace(_SENTINEL.format(i), literal)

    return text


def filter_permissions(text: str, drop_patterns: list[str]) -> str:
    """Drop permission entries naming work-specific systems, then re-serialize.

    These entries are machine-specific convenience (paths into a work repo's
    venv, a vendor's MCP tools). They carry no framework value and would only
    leak internal tooling names, so they are removed rather than templated.
    """
    data = json.loads(text)
    compiled = [re.compile(p, re.IGNORECASE) for p in drop_patterns]

    allow = data.get("permissions", {}).get("allow")
    if isinstance(allow, list):
        kept = [e for e in allow if not any(c.search(e) for c in compiled)]
        dropped = len(allow) - len(kept)
        data["permissions"]["allow"] = kept
        print(f"    dropped {dropped} work-specific permission entries "
              f"({len(kept)} kept)")

    return json.dumps(data, indent=2) + "\n"


def extract_zshrc_function(text: str) -> str:
    """Pull the claude() shell function out of ~/.zshrc.

    Matches from `claude() {` to the first line that is exactly `}`. The
    function is written with consistent indentation, so a closing brace in
    column zero unambiguously ends it.
    """
    lines = text.splitlines()
    start = next(
        (i for i, ln in enumerate(lines) if re.match(r"^\s*claude\s*\(\)\s*\{", ln)),
        None,
    )
    if start is None:
        raise ScrubError("could not find a claude() function in ~/.zshrc")

    end = next((i for i in range(start + 1, len(lines)) if lines[i] == "}"), None)
    if end is None:
        raise ScrubError("claude() function in ~/.zshrc has no closing brace")

    body = "\n".join(lines[start:end + 1])
    header = (
        "# Context-switching wrapper for Claude Code.\n"
        "#\n"
        "# `claude work` and `claude personal` each load a different settings\n"
        "# file, a different set of --add-dir repos, and switch the active gh\n"
        "# account so git operations use the right identity. CLAUDE_CONTEXT is\n"
        "# read by the SessionStart hook to pick the vault destination.\n"
        "#\n"
        "# Paste into ~/.zshrc and fill in the bracketed values.\n\n"
    )
    return header + body + "\n"


def collect_targets(rules: dict, source_root: Path) -> list[tuple[dict, Path, str]]:
    """Resolve file entries to (entry, absolute_src, relative_dst) triples."""
    targets: list[tuple[dict, Path, str]] = []

    for entry in rules.get("files", []):
        if "src_glob" in entry:
            pattern = Path(entry["src_glob"]).expanduser()
            matches = sorted(pattern.parent.glob(pattern.name))
            if not matches:
                print(f"  !  no matches for glob {entry['src_glob']}")
            for match in matches:
                dst = f"{entry['dst_dir']}/{match.name}"
                targets.append((entry, match, dst))
        else:
            targets.append((entry, expand(entry["src"], source_root), entry["dst"]))

    return targets


def generate(out_root: Path, rules: dict) -> list[Path]:
    source_root = Path(rules["meta"]["source_root"]).expanduser()

    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True)

    written: list[Path] = []

    for entry, src, rel_dst in collect_targets(rules, source_root):
        mode = entry["mode"]
        dst = out_root / rel_dst
        dst.parent.mkdir(parents=True, exist_ok=True)

        if mode == "stub":
            print(f"  ~  {rel_dst}  (stubbed — source not published)")
            dst.write_text(entry["stub_text"].lstrip())
            written.append(dst)
            continue

        if not src.exists():
            print(f"  !  MISSING {src} — skipped")
            continue

        text = src.read_text()

        if mode == "json_permissions":
            print(f"  →  {rel_dst}")
            text = filter_permissions(text, entry.get("drop_patterns", []))
        elif mode == "zshrc_function":
            print(f"  →  {rel_dst}  (extracted claude() from {src.name})")
            text = extract_zshrc_function(text)
        elif mode == "template":
            print(f"  →  {rel_dst}")
        else:
            raise ScrubError(f"unknown mode {mode!r} for {rel_dst}")

        text = apply_substitutions(text, rules)

        # Per-file fixups applied after the global rules. launchd needs these:
        # it does NOT expand "~", so a plist rewritten to ~/... looks valid but
        # silently fails to load. Those files convert the tilde back into an
        # explicit {{home}} placeholder the user fills with an absolute path.
        for pattern, replacement in entry.get("post_substitutions", []):
            text = re.sub(pattern, replacement, text)

        dst.write_text(text)
        if src.suffix == ".sh" or src.stat().st_mode & 0o111:
            dst.chmod(0o755)
        written.append(dst)

    return written


def check_forbidden(out_root: Path, rules: dict) -> list[str]:
    """Scan generated output. Any hit is a hard failure.

    Protected literals are masked out before scanning. Without this, `protect`
    and `forbidden` contradict each other: "Workstream" is deliberately kept in
    its generic-English sense, and would otherwise be reported as the employer
    name surviving substitution on every single run.
    """
    violations: list[str] = []
    protected = rules.get("protect", [])

    for rule in rules.get("forbidden", []):
        compiled = re.compile(rule["pattern"])
        for path in sorted(out_root.rglob("*")):
            if not path.is_file():
                continue
            for lineno, line in enumerate(path.read_text().splitlines(), 1):
                for literal in protected:
                    line = line.replace(literal, "")
                match = compiled.search(line)
                if match:
                    rel = path.relative_to(out_root)
                    violations.append(
                        f"{rel}:{lineno}  [{rule['label']}]  "
                        f"matched {match.group(0)[:60]!r}"
                    )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="generate to a temp dir and diff against the committed harness/",
    )
    args = parser.parse_args()

    rules = load_rules()
    final_out = REPO_ROOT / rules["meta"]["output_dir"]

    if args.check:
        tmp = Path(tempfile.mkdtemp()) / "harness"
        print(f"Generating to {tmp} for comparison...\n")
        generate(tmp, rules)
        violations = check_forbidden(tmp, rules)
        if violations:
            print("\nFORBIDDEN PATTERNS FOUND:")
            for v in violations:
                print(f"  {v}")
            return 2

        differences = _diff_trees(final_out, tmp)
        shutil.rmtree(tmp.parent)
        if differences:
            print("\nharness/ is STALE — re-run without --check:")
            for d in differences:
                print(f"  {d}")
            return 1
        print("\nharness/ is up to date and clean.")
        return 0

    print(f"Sanitizing {rules['meta']['source_root']} -> {final_out}\n")
    generate(final_out, rules)

    violations = check_forbidden(final_out, rules)
    if violations:
        print(f"\nFAILED — {len(violations)} forbidden pattern(s) in output:")
        for v in violations:
            print(f"  {v}")
        print("\nOutput left in place for inspection. Fix the source or add a")
        print("rule to harness-scrub.toml, then re-run.")
        return 2

    print(f"\nOK — harness/ generated clean "
          f"({sum(1 for p in final_out.rglob('*') if p.is_file())} files).")
    return 0


def _diff_trees(a: Path, b: Path) -> list[str]:
    """Report files that differ between two trees."""
    diffs: list[str] = []
    if not a.exists():
        return [f"{a} does not exist yet"]

    a_files = {p.relative_to(a) for p in a.rglob("*") if p.is_file()}
    b_files = {p.relative_to(b) for p in b.rglob("*") if p.is_file()}

    for rel in sorted(a_files - b_files):
        diffs.append(f"only in committed harness/: {rel}")
    for rel in sorted(b_files - a_files):
        diffs.append(f"only in freshly generated: {rel}")
    for rel in sorted(a_files & b_files):
        if (a / rel).read_bytes() != (b / rel).read_bytes():
            diffs.append(f"differs: {rel}")

    return diffs


if __name__ == "__main__":
    sys.exit(main())
