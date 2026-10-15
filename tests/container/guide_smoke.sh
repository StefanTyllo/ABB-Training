#!/usr/bin/env bash
# Run from a clean unpacked learner package. Requires only Docker and host Bash.
set -euo pipefail
project="abb-test-guides-$$"
cleanup() { docker compose -p "$project" down --volumes; }
trap cleanup EXIT
docker compose -p "$project" up -d --no-build training
for lab in fw1 fw2 hw1 hw2 t1 t2; do
  for suffix in demo transfer-md transfer-code; do
    workspace="/workspace/work/$lab-$suffix"
    if [ "$suffix" = demo ]; then
      docker compose -p "$project" exec -T training abb prepare "$lab" demo
    else
      docker compose -p "$project" exec -T training abb prepare "$lab" transfer --name "$lab-$suffix"
    fi
    docker compose -p "$project" exec -T --workdir "$workspace" training bash -c 'pwd; test "$PWD" = "$1"' bash "$workspace"
    case "$lab" in
      t1|t2)
        docker compose -p "$project" exec -T --workdir "$workspace" training python -c '
from pathlib import Path
import socket,subprocess,sys,time,urllib.request
with socket.socket() as probe:
 probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
 probe.bind(("127.0.0.1",8765))
log=Path("evidence/guide-server.log").open("w")
p=subprocess.Popen([sys.executable,"server.py","--variant","correct","--port","8765","--state","state.json"],stdout=log,stderr=log)
Path("evidence/guide-server.pid").write_text(str(p.pid))
for attempt in range(100):
 if p.poll() is not None: raise RuntimeError("Owned server exited")
 try:
  urllib.request.urlopen("http://127.0.0.1:8765",timeout=.2).close()
  break
 except OSError:time.sleep(.05)
else:
 p.terminate();p.wait();raise RuntimeError("Readiness timeout")
'
        # A second exec is Terminal B in the same service and exact workspace.
        docker compose -p "$project" exec -T --workdir "$workspace" training python -m pytest browser_preflight.py -q
        if [ "$lab" = t1 ]; then
          docker compose -p "$project" exec -T --workdir "$workspace" training node tools/session_bootstrap.mjs --mode no-login --url http://127.0.0.1:8765 --state .auth/state.json --report evidence/bootstrap.json
        fi
        docker compose -p "$project" exec -T --workdir "$workspace" training python -c '
from pathlib import Path
import os,signal,time
pid=int(Path("evidence/guide-server.pid").read_text())
assert Path(f"/proc/{pid}/cwd").resolve()==Path.cwd()
assert b"server.py" in Path(f"/proc/{pid}/cmdline").read_bytes()
os.kill(pid,signal.SIGTERM)
for attempt in range(100):
 if not Path(f"/proc/{pid}").exists():break
 time.sleep(.05)
'
        ;;
    esac
  done
done
docker compose -p "$project" stop training
docker compose -p "$project" up -d training
docker compose -p "$project" exec -T --workdir /workspace/work/fw1-demo training python -c 'from pathlib import Path; assert Path("case.json").is_file()'
docker compose -p "$project" exec -T training abb export --output /workspace/export/guide-submission.zip
docker compose -p "$project" exec -T training python -c 'import zipfile; z=zipfile.ZipFile("/workspace/export/guide-submission.zip"); assert not any("/.auth/" in name for name in z.namelist()); assert "fw1-demo/case.json" in z.namelist()'
