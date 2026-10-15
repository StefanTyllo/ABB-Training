"""Synthetic device primitives, not a diagnostic/remediation workflow."""
import argparse
import json
from pathlib import Path


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--workdir", type=Path, default=Path(".device"))
    sub = cli.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--case", choices=("demo", "transfer"), required=True)
    read = sub.add_parser("read")
    read.add_argument("--field", choices=("identity", "firmware", "config", "faults"), required=True)
    sub.add_parser("logs")
    sub.add_parser("probe")
    change = sub.add_parser("set")
    change.add_argument("--parameter", choices=("baud",), required=True)
    change.add_argument("--value", type=int, required=True)
    args = cli.parse_args()
    path = args.workdir / "state.json"
    reference = json.loads(Path(__file__).with_name("expected.json").read_text())
    if args.command == "init":
        if path.exists():
            cli.error("state already exists; select a fresh --workdir")
        state = {"case": args.case, "baud": 9600, "events": ["boot: link timeout"]}
        args.workdir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=2)+"\n")
        result = {"initialized": True, "case": args.case}
    else:
        if not path.exists():
            cli.error("initialize the selected workdir first")
        state = json.loads(path.read_text())
        spec = reference[state["case"]]
        ok = state["baud"] == spec["baud"]
        fields = {"identity": {"device_id": spec["device_id"]},
                  "firmware": {"version": spec["firmware"]},
                  "config": {"baud": state["baud"]},
                  "faults": [] if ok else ["LINK_TIMEOUT"]}
        if args.command == "read":
            result = fields[args.field]
        elif args.command == "logs":
            result = state["events"]
        elif args.command == "probe":
            result = {"ok": ok, "status": "reply" if ok else "timeout"}
        else:
            if not 1200 <= args.value <= 115200:
                cli.error("baud must be between 1200 and 115200 inclusive")
            old = state["baud"]
            state["baud"] = args.value
            state["events"].append(f"baud changed: {old} -> {args.value}")
            path.write_text(json.dumps(state, indent=2)+"\n")
            result = {"parameter": "baud", "old": old, "new": args.value}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
