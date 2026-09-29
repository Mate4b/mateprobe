"""Version-pinned historical captures; isolated collection and verified offline replay."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "benchmarks/historical-validator-results"
PROTOCOL = ROOT / "paper/historical-validator-protocol.md"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def probe(sample):
    """Only public payloads enter the third-party validator: no expected labels."""
    if sample["kind"] in ("enum", "refs"):
        from jsonschema import Draft7Validator, RefResolver

        options = {}
        if sample["kind"] == "refs":
            options["resolver"] = RefResolver("", sample["schema"], store=sample["store"])
        errors = list(Draft7Validator(sample["schema"], **options).iter_errors(sample["value"]))
        return {
            "accepted": not errors,
            "complete": True,
            "violations": sorted({str(e.validator) + "@$" for e in errors}),
            "messages": [e.message for e in errors],
            "error": None,
        }
    from marshmallow import ValidationError, fields

    field = fields.Url(schemes={"file"}) if sample["kind"] == "file" else fields.Email()
    try:
        field.deserialize(sample["value"])
    except ValidationError as exc:
        return {
            "accepted": False,
            "complete": True,
            "violations": ["field@$"],
            "messages": [str(exc)],
            "error": None,
        }
    return {"accepted": True, "complete": True, "violations": [], "messages": [], "error": None}


def child(package):
    # This process has only the pinned historical package and its dependencies.
    samples = json.load(sys.stdin)
    results = []
    for sample in samples:
        try:
            results.append(probe(sample))
        except Exception as exc:
            results.append({"error": type(exc).__name__ + ": " + str(exc)})
    print(
        json.dumps(
            {
                "python": platform.python_version(),
                "package_version": importlib.metadata.version(package),
                "results": results,
            },
            sort_keys=True,
        )
    )


def freeze():
    target = OUT / "prepared"
    target.mkdir(exist_ok=False)
    shutil.copyfile(OUT / "frozen-inputs.json", target / "inputs.json")
    shutil.copyfile(PROTOCOL, target / "protocol.md")
    shutil.copyfile(__file__, target / "runner.py.txt")
    write(
        target / "manifest.json",
        {name: sha(target / name) for name in ("inputs.json", "protocol.md", "runner.py.txt")},
    )


def load_prepared():
    target = OUT / "prepared"
    manifest = json.loads((target / "manifest.json").read_text())
    if set(manifest) != {"inputs.json", "protocol.md", "runner.py.txt"}:
        raise ValueError("Unexpected prepared files")
    for name, expected in manifest.items():
        if sha(target / name) != expected:
            raise ValueError("Prepared content changed: " + name)
    if sha(Path(__file__)) != manifest["runner.py.txt"] or sha(PROTOCOL) != manifest["protocol.md"]:
        raise ValueError("Code or protocol differs from frozen source")
    return json.loads((target / "inputs.json").read_text())


def collect(work, output, lock_from=None):
    data = load_prepared()
    work.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=False)
    records = {}
    for candidate in data["candidates"]:
        if candidate["decision"] != "include":
            continue
        pairs = data["authored_inputs"][candidate["id"]]
        samples = [pair[side] for pair in pairs for side in ("baseline", "variant")]
        records[candidate["id"]] = {}
        for version in (candidate["before"], candidate["after"]):
            name = candidate["package"] + "-" + version
            env = work / name
            if env.exists():
                raise ValueError("Use a fresh environment directory: " + str(env))
            venv.EnvBuilder(with_pip=True, symlinks=True).create(env)
            python = str(env / "bin/python")
            pip_report = env / "install.json"
            install_args = [candidate["package"] + "==" + version]
            if lock_from:
                install_args = ["-r", str(lock_from / (name + ".lock.txt"))]
            install = subprocess.run(
                [
                    python,
                    "-m",
                    "pip",
                    "--disable-pip-version-check",
                    "install",
                    "--report",
                    str(pip_report),
                    *install_args,
                ],
                capture_output=True,
                text=True,
                timeout=180,
            )
            record = {"install_returncode": install.returncode}
            if install.returncode:
                record["setup_error"] = install.stderr
                records[candidate["id"]][version] = record
                continue
            installed = json.loads(pip_report.read_text())
            record["artifacts"] = [
                {
                    "name": item["metadata"]["name"],
                    "version": item["metadata"]["version"],
                    "url": item["download_info"]["url"],
                    "hashes": item["download_info"]["archive_info"].get("hashes", {}),
                }
                for item in installed["install"]
            ]
            lock = subprocess.check_output([python, "-m", "pip", "freeze"], text=True)
            (output / (name + ".lock.txt")).write_text(lock)
            record["lock_sha256"] = sha(output / (name + ".lock.txt"))
            proc = subprocess.run(
                [
                    python,
                    "-I",
                    str(Path(__file__).resolve()),
                    "child",
                    "--package",
                    candidate["package"],
                ],
                input=json.dumps(samples),
                capture_output=True,
                text=True,
                timeout=30,
            )
            record.update(
                {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
            )
            if proc.returncode == 0:
                record["payload"] = json.loads(proc.stdout)
            records[candidate["id"]][version] = record
            print(name, "captured", flush=True)
    write(output / "captured.json", records)
    write(
        output / "manifest.json",
        {
            "prepared_manifest_sha256": sha(OUT / "prepared/manifest.json"),
            "files": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()},
        },
    )


def replay(captured, output):
    from narrative_contracts.model import digest
    from narrative_contracts.mutations import Relation, Validity
    from narrative_contracts.validator_audit import AuditCase, Obligation, Verdict, audit_validator

    data = load_prepared()
    manifest = json.loads((captured / "manifest.json").read_text())
    if manifest["prepared_manifest_sha256"] != sha(OUT / "prepared/manifest.json"):
        raise ValueError("Capture does not match preparation")
    if "captured.json" not in manifest["files"] or any(
        Path(n).name != n for n in manifest["files"]
    ):
        raise ValueError("Invalid capture manifest")
    for name, expected in manifest["files"].items():
        if sha(captured / name) != expected:
            raise ValueError("Capture changed: " + name)
    records = json.loads((captured / "captured.json").read_text())
    reports, results = {}, []
    included = [c for c in data["candidates"] if c["decision"] == "include"]
    if set(records) != {c["id"] for c in included}:
        raise ValueError("Missing or extra candidate capture")
    for candidate in included:
        pairs = data["authored_inputs"][candidate["id"]]
        versions = records[candidate["id"]]
        outcomes = {}
        for version in (candidate["before"], candidate["after"]):
            record = versions[version]
            if record["install_returncode"] or record["returncode"]:
                outcomes[version] = {"execution": "unavailable"}
                continue
            payload = record["payload"]
            if payload != json.loads(record["stdout"]) or payload["package_version"] != version:
                raise ValueError("Captured version or raw output mismatch")
            if len(payload["results"]) != 2 * len(pairs):
                raise ValueError("Incomplete paired capture")
            lookup = {}
            for pair_index, pair in enumerate(pairs):
                for side_index, side in enumerate(("baseline", "variant")):
                    key = digest(pair[side])
                    observed = payload["results"][pair_index * 2 + side_index]
                    if key in lookup and lookup[key] != observed:
                        raise ValueError("Inconsistent repeated baseline capture")
                    lookup[key] = observed

            def adapter(sample):
                record = lookup[digest(sample)]
                if record["error"]:
                    raise RuntimeError(record["error"])
                return Verdict(
                    record["accepted"],
                    tuple(record["violations"]),
                    record["complete"],
                    tuple(record["messages"]),
                )

            cases = tuple(
                AuditCase(
                    p["id"],
                    candidate["id"],
                    p["baseline"],
                    p["variant"],
                    Relation(p["relation"]),
                    tuple(p["expected"]),
                    Validity.VALID,
                    "Authored minimal reproduction of " + candidate["source"],
                )
                for p in pairs
            )
            report = audit_validator(
                adapter,
                cases,
                obligations=(Obligation(candidate["id"], candidate["behavior"]),),
                validator_id=f"{candidate['package']}/{version}",
            )
            reports[candidate["id"] + "/" + version] = report.to_dict()
            outcomes[version] = {c.id: c.outcome for c in report.cases}
        trigger, control = pairs
        before, after = outcomes[candidate["before"]], outcomes[candidate["after"]]
        desired = "detected" if trigger["relation"] == "violation" else "preserved"
        reproduced = (
            before.get(trigger["id"]) in ("survived", "regressed", "error")
            and after.get(trigger["id"]) == desired
            and before.get(control["id"]) == after.get(control["id"]) == "preserved"
        )
        results.append(
            {
                "id": candidate["id"],
                "source": candidate["source"],
                "before_version": candidate["before"],
                "after_version": candidate["after"],
                "outcomes": outcomes,
                "fix_reproduced": reproduced,
            }
        )
    summary = {
        "schema_version": 1,
        "screened": len(data["candidates"]),
        "included": len(included),
        "excluded": len(data["candidates"]) - len(included),
        "fixes_reproduced": sum(r["fix_reproduced"] for r in results),
        "results": results,
    }
    output.mkdir(parents=True, exist_ok=False)
    write(output / "summary.json", summary)
    write(output / "audit-reports.json", reports)
    print(json.dumps(summary, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "collect", "replay", "child"))
    parser.add_argument("--network", action="store_true")
    parser.add_argument("--work", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--captured", type=Path)
    parser.add_argument("--lock-from", type=Path)
    parser.add_argument("--package")
    args = parser.parse_args()
    if args.action == "child":
        child(args.package)
    elif args.action == "freeze":
        freeze()
    elif args.action == "collect":
        if not args.network or args.work is None or args.output is None:
            parser.error("collect requires --network, --work and --output")
        collect(args.work, args.output, args.lock_from)
    else:
        if args.captured is None or args.output is None:
            parser.error("replay requires --captured and --output")
        replay(args.captured, args.output)


if __name__ == "__main__":
    main()
