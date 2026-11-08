"""Prepare synchronized plugin versions for the GitHub Actions release job."""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

PLUGIN = Path(".claude-plugin/plugin.json")


def _git(*args: str) -> str:
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True, env=environment
    )
    return result.stdout.strip()


def _release_state(source: str) -> str:
    if _git("rev-parse", "HEAD") == source:
        return "new"
    parent = _git("rev-parse", "HEAD^")
    message = _git("log", "-1", "--format=%B")
    if parent == source and message.startswith("Release ") and f"Source-Commit: {source}" in message.splitlines():
        return "retry"
    return "stale"


def _parts(value: object) -> tuple[int, int, int]:
    if not isinstance(value, str) or (match := re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", value)) is None:
        raise ValueError(f"version must be major.minor.patch: {value!r}")
    return int(match[1]), int(match[2]), int(match[3])


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return value


def _version(manifest: dict[str, object]) -> str:
    return ".".join(map(str, _parts(manifest.get("version"))))


def _prepare_version(previous: str) -> str:
    # NOTE: README.md names .claude-plugin/plugin.json as the version source of truth.
    paths = [PLUGIN, Path(".codex-plugin/plugin.json"), Path(".claude-plugin/marketplace.json")]
    manifests = [_read_json(path) for path in paths]
    if any(manifest.get("name") != "clod-soul" for manifest in manifests[:2]):
        raise ValueError("plugin manifests must be named clod-soul")
    current = _version(manifests[0])
    baseline = _version(json.loads(_git("show", f"{previous}:{PLUGIN}")))
    current_parts, baseline_parts = _parts(current), _parts(baseline)
    if current_parts < baseline_parts:
        raise ValueError(f"version decreased from {baseline} to {current}")
    version = current if current_parts > baseline_parts else f"{current_parts[0]}.{current_parts[1]}.{current_parts[2] + 1}"
    plugins = manifests[2].get("plugins")
    if not isinstance(plugins, list):
        raise TypeError("marketplace must contain a plugins array")
    registrations = [
        item for item in plugins if isinstance(item, dict) and item.get("name") == "clod-soul"
    ]
    if len(registrations) != 1:
        raise ValueError("marketplace must register clod-soul exactly once")
    plugin = registrations[0]
    plugin["version"] = version
    for manifest in manifests[:2]:
        manifest["version"] = version

    for path, manifest in zip(paths, manifests, strict=True):
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return version


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--previous", required=True, help="Branch HEAD before this push")
    args = parser.parse_args()
    for name in ("source", "previous"):
        if re.fullmatch(r"[0-9a-f]{40}", getattr(args, name)) is None:
            parser.error(f"{name} must be a full Git commit SHA")
    try:
        output_path = Path(os.environ["GITHUB_OUTPUT"])
        state = _release_state(args.source)
        version = _prepare_version(args.previous) if state == "new" else _version(_read_json(PLUGIN))
        with output_path.open("a", encoding="utf-8") as output:
            output.write(f"state={state}\nversion={version}\n")
    except (KeyError, OSError, subprocess.CalledProcessError, TypeError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
