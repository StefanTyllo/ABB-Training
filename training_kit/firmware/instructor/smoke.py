"""Instructor acceptance: starter defects must exist; corrected isolated copy must pass."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def run(*args, ok=True):
    p = subprocess.run(list(map(str, args)), text=True, capture_output=True)
    assert (p.returncode == 0) == ok, (args, p.stdout, p.stderr)
    return json.loads(p.stdout) if p.stdout.strip() else None

def packet(seq, value):
    b = [0xA5, 2, seq, value & 255, (value >> 8) & 255]
    check = 0
    for byte in b:
        check ^= byte
    return bytes(b + [check]).hex()

def grade(exe):
    cases = [([], []), ([packet(7, -123)], [{"sequence": 7, "value": -123}])]
    for value in (-32768, -2048, -1, 0, 165, 32767):
        frame = packet(42, value)
        expected = [{"sequence": 42, "value": value}]
        cases.append(([frame], expected))
        for cut in range(2, 12, 2):
            cases.append(([frame[:cut], "", frame[cut:]], expected))
        cases.append(([frame[i:i+2] for i in range(0, 12, 2)], expected))
    a, b = packet(7, -123), packet(42, -2048)
    both = [{"sequence": 7, "value": -123}, {"sequence": 42, "value": -2048}]
    cases += [([a+b], both), (["00a500"+a], both[:1]),
              ([a[:-2]+"00"+b], both[1:]), (["a502"+a], both[:1]),
              (["a50207"], []), ([packet(0xA5, 0xA5)], [{"sequence":165,"value":165}])]
    failures = []
    for chunks, expected in cases:
        actual = run(exe, *chunks)
        if actual != expected:
            failures.append((chunks, expected, actual))
    for invalid in ("a", "zz", "00" * 4097):
        run(exe, invalid, ok=False)
    return failures, len(cases)

def main():
    if len(sys.argv) == 2:
        failures, count = grade(Path(sys.argv[1]).resolve())
        print(json.dumps({"cases": count, "failures": failures}, indent=2))
        return bool(failures)
    assert (ROOT / "fw1/device.py").exists(), "FW1 starter not implemented"
    with tempfile.TemporaryDirectory(dir=ROOT / "instructor") as temp:
        work = Path(temp)
        for case, expected in (("demo", 19200), ("transfer", 38400)):
            device = [sys.executable, ROOT/"fw1/device.py", "--workdir", work/case]
            run(*device, "probe", ok=False)
            run(*device, "init", "--case", case)
            run(*device, "init", "--case", case, ok=False)
            identity = "SIM-017" if case == "demo" else "SIM-083"
            assert run(*device, "read", "--field", "identity") == {"device_id": identity}
            assert run(*device, "read", "--field", "firmware") == {"version": "1.4.2"}
            assert run(*device, "read", "--field", "faults") == ["LINK_TIMEOUT"]
            assert run(*device, "read", "--field", "config")["baud"] == 9600
            assert not run(*device, "probe")["ok"]
            before = (work/case/"state.json").read_bytes()
            for parameter, value in (("address", "1"), ("baud", "0"), ("baud", "999999")):
                run(*device, "set", "--parameter", parameter, "--value", value, ok=False)
                assert (work/case/"state.json").read_bytes() == before
            run(*device, "set", "--parameter", "baud", "--value", expected)
            assert run(*device, "probe")["ok"]
            assert run(*device, "read", "--field", "faults") == []
            assert len(run(*device, "logs")) == 2
        source = (ROOT/"fw2/parser.c").read_text()
        def build(src, name):
            path = work / (name+".c")
            path.write_text(src)
            exe = work/name
            run("gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", ROOT/"fw2",
                path, ROOT/"fw2/main.c", "-o", exe)
            return exe
        seeded = build(source, "seeded")
        assert run(seeded, "a5020785ffda") == [{"sequence":7,"value":65413}]
        assert run(seeded, "a50207", "85ffda") == []
        failures, count = grade(seeded)
        assert failures, "grader must reject seeded defects"
        corrected = source.replace("    p->used = 0; /* seeded: chunk boundary */\n", "")
        corrected = corrected.replace("int value = raw;", "int value = raw >= 32768 ? (int)raw - 65536 : (int)raw;")
        failures, count = grade(build(corrected, "corrected"))
        assert not failures, failures
        print(f"PASS: FW1 demo/transfer; FW2 seeded failures and {count} corrected cases")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
