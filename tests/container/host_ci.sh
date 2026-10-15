#!/usr/bin/env bash
set -euo pipefail
image=$(docker image inspect abb-training-facilitator:dev --format '{{.Id}}')
artifact=${1:?Provide a fresh absolute path for the disposable image archive}
test ! -e "$artifact"
docker run --rm --network none -e ABB_TEST_AUTH_SENTINEL=ABB_SYNTHETIC_SENTINEL "$image" python -c 'import os; assert os.environ["ABB_TEST_AUTH_SENTINEL"]=="ABB_SYNTHETIC_SENTINEL"'
docker run --rm --network none "$image" python -c 'import os; from pathlib import Path; assert "ABB_TEST_AUTH_SENTINEL" not in os.environ; assert not Path("/run/secrets/copilot_token").exists(); assert not Path("/home/learner/.copilot/config.json").exists(); assert not Path("/home/learner/.codex/auth.json").exists()'
status=0
docker run --rm --network none "$image" python /opt/abb/runtime/ci.py -- python -c 'raise SystemExit(7)' || status=$?
test "$status" -eq 7
docker history --no-trunc "$image" | docker run --rm -i --network none "$image" python -c 'import sys; assert "ABB_SYNTHETIC_SENTINEL" not in sys.stdin.read()'
docker save --output "$artifact" "$image"
docker run --rm --network none --mount "type=bind,src=$artifact,dst=/artifact,readonly" "$image" python -c 'import hashlib; print("image archive sha256:",hashlib.file_digest(open("/artifact","rb"),"sha256").hexdigest())'
docker load --input "$artifact"
test "$(docker image inspect "$image" --format '{{.Id}}')" = "$image"
