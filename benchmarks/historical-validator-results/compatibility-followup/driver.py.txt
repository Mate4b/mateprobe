"""Explicit compatibility follow-up; preserves the original historical captures."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmarks/historical-validator-results"
OUT = BASE / "compatibility-followup"
spec = importlib.util.spec_from_file_location(
    "historical_base", ROOT / "benchmarks/historical_validator_study.py"
)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.OUT = OUT
base.PROTOCOL = ROOT / "paper/historical-followup-protocol.md"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    OUT.mkdir(exist_ok=False)
    requirements = OUT / "requirements"
    requirements.mkdir()
    data = json.loads((BASE / "prepared/inputs.json").read_text())
    for c in data["candidates"]:
        if c["id"] == "jsonschema-bool-ref-cache":
            c["before"] = "4.17.1"
            c["reason"] += (
                " Follow-up uses available 4.17.1; initial 4.17.2 could not be installed."
            )
        if c["decision"] != "include":
            continue
        for version in (c["before"], c["after"]):
            name = c["package"] + "-" + version + ".lock.txt"
            original = BASE / "captured" / name
            if version == "4.17.1":
                content = (
                    (BASE / "captured/jsonschema-4.17.3.lock.txt")
                    .read_text()
                    .replace("jsonschema==4.17.3", "jsonschema==4.17.1")
                )
            else:
                content = original.read_text()
            if c["package"] == "jsonschema" and version.startswith("3."):
                content += "setuptools==70.3.0\n"
            (requirements / name).write_text(content)
    data["followup_driver_sha256"] = sha(Path(__file__))
    data["requirements_sha256"] = {p.name: sha(p) for p in requirements.iterdir()}
    data["parent_capture_manifest_sha256"] = sha(BASE / "captured/manifest.json")
    (OUT / "frozen-inputs.json").write_text(
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )
    base.freeze()


def verify():
    data = base.load_prepared()
    if sha(Path(__file__)) != data["followup_driver_sha256"]:
        raise ValueError("Follow-up driver changed")
    for name, expected in data["requirements_sha256"].items():
        if Path(name).name != name or sha(OUT / "requirements" / name) != expected:
            raise ValueError("Follow-up requirements changed")
    if sha(BASE / "captured/manifest.json") != data["parent_capture_manifest_sha256"]:
        raise ValueError("Parent capture identity changed")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("prepare", "collect", "replay"))
    p.add_argument("--network", action="store_true")
    p.add_argument("--work", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--captured", type=Path)
    args = p.parse_args()
    if args.action == "prepare":
        prepare()
        return
    verify()
    if args.action == "collect":
        if not args.network or args.work is None or args.output is None:
            p.error("collect requires --network, --work and --output")
        base.collect(args.work, args.output, OUT / "requirements")
    else:
        if args.captured is None or args.output is None:
            p.error("replay requires --captured and --output")
        base.replay(args.captured, args.output)


if __name__ == "__main__":
    main()
