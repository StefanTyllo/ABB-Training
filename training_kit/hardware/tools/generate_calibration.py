#!/usr/bin/env python3
"""Low-level nominal calibration emitter; does not assess circuit safety or tolerance."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def calibration_from_config(config):
    """Emit nominal inverse gain and a digest of the complete source configuration."""
    required = ("r_top_ohm", "r_bottom_ohm", "resistor_tolerance_fraction", "c_farad", "vin_max_v", "adc_max_v")
    for key in required:
        value = config[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"{key} must be a finite positive number")
    if config["resistor_tolerance_fraction"] >= 1:
        raise ValueError("resistor_tolerance_fraction must be less than 1")
    if not isinstance(config["board_id"], str) or not config["board_id"]:
        raise ValueError("board_id must be a nonempty string")
    if not isinstance(config["source_revision"], str) or not config["source_revision"]:
        raise ValueError("source_revision must be a nonempty string")
    canonical = json.dumps(config, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    inverse_gain = (config["r_top_ohm"] + config["r_bottom_ohm"]) / config["r_bottom_ohm"]
    return {"schema_version": 1, "board_id": config["board_id"], "source_revision": config["source_revision"],
            "inverse_gain": inverse_gain, "source_sha256": hashlib.sha256(canonical).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replace", action="store_true", help="explicitly replace an existing derived output")
    args = parser.parse_args()
    if args.output.resolve() == args.config.resolve():
        parser.error("source configuration cannot be the output")
    if args.output.exists() and not args.replace:
        parser.error("output exists; use --replace for an authorized derived artifact")
    if args.output.is_symlink():
        parser.error("refusing symlink output")
    try:
        result = calibration_from_config(json.loads(args.config.read_text(encoding="utf-8")))
        encoded = json.dumps(result, indent=2, allow_nan=False) + "\n"
    except (KeyError, ValueError, TypeError, OSError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w" if args.replace else "x", encoding="utf-8") as stream:
        stream.write(encoded)
    print(f"Wrote nominal calibration to {args.output}")


if __name__ == "__main__":
    main()
