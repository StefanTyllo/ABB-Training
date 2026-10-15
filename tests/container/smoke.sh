#!/usr/bin/env bash
set -euo pipefail
project="abb-test-persistence-$$"
other="abb-test-isolation-$$"
cleanup() {
  docker compose -p "$project" down --volumes
  docker compose -p "$other" down --volumes
}
trap cleanup EXIT
for participant in "$project" "$other"; do
  docker compose -p "$participant" up -d --no-build training
done
docker compose -p "$project" exec -T training abb prepare fw1 demo --name 'work with spaces'
docker compose -p "$project" exec -T training python -c 'from pathlib import Path; Path("/workspace/work/work with spaces/evidence/marker").write_text("original-work"); Path("/home/learner/.codex/abb-volume-probe").write_text("SYNTHETIC_ONLY")'
docker compose -p "$project" exec -T --workdir '/workspace/work/work with spaces' training bash -c 'test -f evidence/marker'
docker compose -p "$project" stop training
docker compose -p "$project" up -d training
docker compose -p "$project" exec -T training python -c 'from pathlib import Path; assert Path("/workspace/work/work with spaces/evidence/marker").read_text()=="original-work"; assert Path("/home/learner/.codex/abb-volume-probe").read_text()=="SYNTHETIC_ONLY"'
docker compose -p "$other" exec -T training python -c 'from pathlib import Path; assert not Path("/workspace/work/work with spaces").exists(); assert not Path("/home/learner/.codex/abb-volume-probe").exists()'
docker compose -p "$project" build training
docker compose -p "$project" up -d training
docker compose -p "$project" exec -T training python -c 'from pathlib import Path; assert Path("/workspace/work/work with spaces/evidence/marker").read_text()=="original-work"; assert Path("/home/learner/.codex/abb-volume-probe").read_text()=="SYNTHETIC_ONLY"'
docker compose -p "$project" exec -T training abb export --output /workspace/export/smoke.zip
docker compose -p "$project" exec -T training python -c 'import zipfile; z=zipfile.ZipFile("/workspace/export/smoke.zip"); assert z.read("work with spaces/evidence/marker")==b"original-work"'
