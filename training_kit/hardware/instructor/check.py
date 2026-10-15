#!/usr/bin/env python3
"""Instructor-only independent checks; not copied into participant starters."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def quantity(text):
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*(kOhm|Ohm|nF|uF|F)\s*", text)
    if not match:
        raise ValueError(f"unsupported quantity: {text}")
    amount, unit = match.groups()
    scales = {"kOhm": ("resistance", 1000), "Ohm": ("resistance", 1), "nF": ("capacitance", 1e-9), "uF": ("capacitance", 1e-6), "F": ("capacitance", 1)}
    dimension, scale = scales[unit]
    return dimension, float(amount) * scale


def check(lab, case, workspace):
    expected = read(ROOT / "instructor/expected.json")[f"{lab}/{case}"]
    original = ROOT / "fixtures" / lab / case
    failures = []
    def require(condition, message):
        if not condition:
            failures.append(message)
    for source in (original / "source").iterdir():
        actual = workspace / "source" / source.name
        require(actual.is_file() and actual.read_bytes() == source.read_bytes(), f"immutable source changed: {source.name}")
    report = read(workspace / "report.json")
    for key, value in (("schema_version", 1), ("lab", lab), ("case", case), ("board_id", expected["board_id"]), ("status", expected["status"])):
        require(report.get(key) == value, f"report {key} must be {value!r}")
    findings = report.get("findings", [])
    require(isinstance(findings, list), "findings must be an array")
    findings = findings if isinstance(findings, list) else []
    codes = {item.get("code") for item in findings if isinstance(item, dict)}
    for code in expected["finding_codes"]:
        require(code in codes, f"missing finding code: {code}")
    for item in findings:
        require(isinstance(item, dict) and bool(item.get("evidence")) and bool(item.get("explanation")), "every finding requires evidence and explanation")
    require(isinstance(report.get("changed_files"), list), "changed_files must be an array")
    require(isinstance(report.get("assumptions"), list) and bool(report["assumptions"]), "assumptions must be a nonempty array")
    if lab == "hw1":
        netlist = workspace / "derived/netlist.json"
        if case == "transfer":
            require(netlist.read_bytes() == (original / "derived/netlist.json").read_bytes(), "blocked case must preserve derived netlist")
            require(report.get("changed_files") == [], "blocked case changed_files must be empty")
        else:
            actual = read(netlist)
            source = read(original / "source/schematic.json")
            require(actual.get("board_id") == source["board_id"] and actual.get("source_revision") == source["source_revision"], "netlist provenance does not match approved source")
            components = actual.get("components", [])
            indexed = {item["ref"]: item for item in components}
            require(len(components) == len(indexed) == len(source["components"]), "component count or duplicate reference error")
            require(set(indexed) == {item["ref"] for item in source["components"]}, "component reference set differs")
            for source_component in source["components"]:
                ref = source_component["ref"]
                component = indexed.get(ref, {})
                require(component.get("kind") == source_component["kind"] and component.get("pins") == source_component["pins"], f"kind/pin mapping mismatch: {ref}")
                if source_component["kind"] == "ic":
                    equivalent = component.get("value") == source_component["value"]
                else:
                    left = quantity(component.get("value", ""))
                    right = quantity(source_component["value"])
                    equivalent = left[0] == right[0] and math.isclose(left[1], right[1], rel_tol=1e-12)
                require(equivalent, f"value mismatch: {ref}")
            require(report.get("changed_files") == ["derived/netlist.json"], "changed_files must identify the reconciled netlist")
    else:
        calculations = report.get("calculations", {})
        for key, value in expected["calculations"].items():
            actual = calculations.get(key)
            require(isinstance(actual, (int, float)) and not isinstance(actual, bool) and math.isclose(actual, value, rel_tol=1e-8, abs_tol=1e-9), f"calculation differs: {key}")
        config = read(original / "source/circuit.json")
        canonical = json.dumps(config, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        calibration = read(workspace / "derived/calibration.json")
        require(calibration.get("inverse_gain") == expected["calculations"]["inverse_gain"], "nominal inverse gain differs")
        require(calibration.get("source_sha256") == hashlib.sha256(canonical).hexdigest(), "calibration source digest differs")
        require(calibration.get("source_revision") == config["source_revision"] and calibration.get("board_id") == config["board_id"], "calibration provenance differs")
        require(report.get("changed_files") == ["derived/calibration.json"], "changed_files must identify regenerated calibration")
        generator = workspace / "tools/generate_calibration.py"
        require(generator.read_bytes() == (ROOT / "tools/generate_calibration.py").read_bytes(), "provided generator changed")
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab", choices=("hw1", "hw2"), required=True)
    parser.add_argument("--case", choices=("demo", "transfer"), required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    try:
        failures = check(args.lab, args.case, args.workspace)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        failures = [f"invalid or missing submission: {exc}"]
    if failures:
        print("CHECK FAILED\n" + "\n".join(f"- {item}" for item in failures))
        raise SystemExit(1)
    print(f"CHECK PASSED: {args.lab}/{args.case} synthetic exercise criteria")


if __name__ == "__main__":
    main()
