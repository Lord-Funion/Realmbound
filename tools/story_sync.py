#!/usr/bin/env python3
"""Build and synchronize Realmbound's cross-port story source bundle.

The repository currently keeps the executable story in different languages and,
for C++ and legacy, on different branches.  This tool makes one deterministic
JSON file the canonical bundle.  Each port entry contains the complete source
file that implements that port's story, split into lines for readable diffs.

Typical workflow:

    python tools/story_sync.py extract
    # edit story/realmbound_story.json
    python tools/story_sync.py apply --port python --port web
    python tools/story_sync.py check

For a port that lives on another branch, check out that branch (or a worktree)
and pass --root plus --bundle as needed.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "story" / "realmbound_story.json"
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class PortSpec:
    name: str
    branch: str
    path: str
    local_on_source_branch: bool = False
    optional: bool = False


PORTS: tuple[PortSpec, ...] = (
    PortSpec("python", "main", "text_adventure/story.py", local_on_source_branch=True),
    PortSpec("web", "main", "web/app.js", local_on_source_branch=True),
    PortSpec("cpp", "cpp-port", "cpp/adventure_game.cpp"),
    PortSpec("legacy", "legacy", "main.py", optional=True),
)


def run_git(*args: str, cwd: Path = ROOT, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise RuntimeError(f"git {' '.join(args)}: {message}")
    return result.stdout


def current_branch(root: Path = ROOT) -> str:
    return run_git("branch", "--show-current", cwd=root).strip()


def available_ref(branch: str) -> str | None:
    for candidate in (branch, f"origin/{branch}"):
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", candidate],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode == 0:
            return candidate
    return None


def read_source(spec: PortSpec) -> tuple[str, str, str]:
    """Return source text, source ref label, and blob SHA for a port."""
    local_path = ROOT / spec.path
    branch = current_branch()

    if spec.local_on_source_branch and local_path.exists():
        text = local_path.read_text(encoding="utf-8")
        blob_sha = run_git("hash-object", spec.path).strip()
        return text, branch or "working-tree", blob_sha

    ref = available_ref(spec.branch)
    if ref is None:
        if spec.optional:
            raise FileNotFoundError(f"optional branch {spec.branch!r} is unavailable")
        raise RuntimeError(
            f"Cannot find branch {spec.branch!r}. Fetch all branches first with "
            f"'git fetch origin {spec.branch}'."
        )

    object_name = f"{ref}:{spec.path}"
    result = subprocess.run(
        ["git", "show", object_name],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        if spec.optional:
            raise FileNotFoundError(f"optional source {object_name!r} is unavailable")
        raise RuntimeError(result.stderr.strip() or f"Cannot read {object_name}")
    blob_sha = run_git("rev-parse", object_name).strip()
    return result.stdout, spec.branch, blob_sha


def literal_assignment(module: ast.Module, name: str) -> Any | None:
    for node in module.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets: Iterable[ast.expr]
        value: ast.expr | None
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        else:
            targets = (node.target,)
            value = node.value
        if value is None:
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in targets):
            continue
        try:
            return ast.literal_eval(value)
        except (ValueError, TypeError):
            return None
    return None


def parse_story_metadata(python_source: str) -> tuple[list[str], dict[str, str]]:
    module = ast.parse(python_source)
    raw_order = literal_assignment(module, "SCENE_ORDER")
    scene_order = list(raw_order) if isinstance(raw_order, (list, tuple)) else []

    titles: dict[str, str] = {}
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "SCENE_TITLES" for target in node.targets):
            continue
        if not isinstance(node.value, ast.Dict):
            continue
        for key_node, value_node in zip(node.value.keys, node.value.values):
            if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                if isinstance(value_node, ast.Constant) and isinstance(value_node.value, str):
                    titles[key_node.value] = value_node.value
        break
    return scene_order, titles


def source_payload(text: str) -> dict[str, Any]:
    return {
        "source_lines": text.splitlines(),
        "trailing_newline": text.endswith("\n"),
    }


def payload_text(payload: dict[str, Any]) -> str:
    lines = payload.get("source_lines")
    if not isinstance(lines, list) or any(not isinstance(line, str) for line in lines):
        raise ValueError("Port source_lines must be a list of strings.")
    text = "\n".join(lines)
    if payload.get("trailing_newline", True):
        text += "\n"
    return text


def build_bundle() -> dict[str, Any]:
    port_entries: dict[str, Any] = {}
    python_source: str | None = None

    for spec in PORTS:
        try:
            text, source_ref, blob_sha = read_source(spec)
        except FileNotFoundError:
            continue
        entry = {
            "branch": spec.branch,
            "source_ref": source_ref,
            "path": spec.path,
            "blob_sha": blob_sha,
            **source_payload(text),
        }
        port_entries[spec.name] = entry
        if spec.name == "python":
            python_source = text

    if python_source is None:
        raise RuntimeError("The Python story source is required to build the bundle.")

    scene_order, scene_titles = parse_story_metadata(python_source)
    return {
        "schema_version": SCHEMA_VERSION,
        "game": "Realmbound",
        "purpose": (
            "Canonical cross-port story source. Edit this file, then use "
            "tools/story_sync.py to regenerate the native port files."
        ),
        "scene_order": scene_order,
        "scene_titles": scene_titles,
        "ports": port_entries,
    }


def load_bundle(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported story bundle schema {data.get('schema_version')!r}; "
            f"expected {SCHEMA_VERSION}."
        )
    if not isinstance(data.get("ports"), dict):
        raise ValueError("Story bundle is missing its ports object.")
    return data


def write_bundle(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(rendered, encoding="utf-8")


def normalized(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def command_extract(bundle_path: Path) -> int:
    data = build_bundle()
    write_bundle(bundle_path, data)
    print(f"Wrote {bundle_path.relative_to(ROOT)} with {len(data['ports'])} ports.")
    for name, entry in data["ports"].items():
        print(f"  {name}: {entry['branch']}:{entry['path']} ({len(entry['source_lines'])} lines)")
    return 0


def command_check(bundle_path: Path) -> int:
    existing = load_bundle(bundle_path)
    fresh = build_bundle()
    if normalized(existing) == normalized(fresh):
        print("Shared story bundle matches all configured port sources.")
        return 0

    print("Shared story bundle is out of sync.", file=sys.stderr)
    print("Run: python tools/story_sync.py extract", file=sys.stderr)
    return 1


def selected_specs(names: list[str]) -> list[PortSpec]:
    by_name = {spec.name: spec for spec in PORTS}
    unknown = [name for name in names if name not in by_name]
    if unknown:
        raise ValueError(f"Unknown port(s): {', '.join(unknown)}")
    return [by_name[name] for name in names]


def command_apply(bundle_path: Path, names: list[str], root: Path, force: bool) -> int:
    data = load_bundle(bundle_path)
    branch = current_branch(root)

    for spec in selected_specs(names):
        entry = data["ports"].get(spec.name)
        if not isinstance(entry, dict):
            raise ValueError(f"Bundle has no source for port {spec.name!r}.")
        if not force and branch and branch != spec.branch and not branch.startswith("agent/"):
            raise RuntimeError(
                f"Port {spec.name!r} belongs to branch {spec.branch!r}, but the target "
                f"worktree is on {branch!r}. Use --force only when this is intentional."
            )
        target = root / spec.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload_text(entry), encoding="utf-8")
        print(f"Applied {spec.name} story source to {target}.")
    return 0


def command_summary(bundle_path: Path) -> int:
    data = load_bundle(bundle_path)
    print(f"{data.get('game', 'Story')} schema {data.get('schema_version')}")
    print(f"Scenes: {len(data.get('scene_order', []))}")
    for name, entry in data["ports"].items():
        print(
            f"  {name}: {entry.get('branch')}:{entry.get('path')} "
            f"({len(entry.get('source_lines', []))} lines, {entry.get('blob_sha')})"
        )
    return 0


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("extract", "check", "apply", "summary"),
        help="Operation to perform.",
    )
    parser.add_argument(
        "--bundle",
        type=Path,
        default=DEFAULT_BUNDLE,
        help=f"Bundle path (default: {DEFAULT_BUNDLE.relative_to(ROOT)}).",
    )
    parser.add_argument(
        "--port",
        action="append",
        dest="ports",
        choices=tuple(spec.name for spec in PORTS),
        help="Port to apply; repeat for multiple ports.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Target repository/worktree root for apply.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow applying a port to a worktree on a different branch.",
    )
    return parser


def main() -> int:
    args = make_parser().parse_args()
    bundle_path = args.bundle.resolve()
    if args.command == "extract":
        return command_extract(bundle_path)
    if args.command == "check":
        return command_check(bundle_path)
    if args.command == "summary":
        return command_summary(bundle_path)
    ports = args.ports or ["python", "web"]
    return command_apply(bundle_path, ports, args.root.resolve(), args.force)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, SyntaxError) as exc:
        print(f"story-sync: {exc}", file=sys.stderr)
        raise SystemExit(2)
