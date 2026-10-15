$ErrorActionPreference = 'Stop'
$project = "abb-test-persistence-$PID"
$other = "abb-test-isolation-$PID"
function Docker-Checked {
    & docker @args
    if ($LASTEXITCODE -ne 0) { throw "Docker exited with $LASTEXITCODE" }
}
try {
    foreach ($participant in @($project, $other)) {
        Docker-Checked compose -p $participant up -d --no-build training
    }
    Docker-Checked compose -p $project exec -T training abb prepare fw1 demo --name 'work with spaces'
    Docker-Checked compose -p $project exec -T training python -c 'from pathlib import Path; Path("/workspace/work/work with spaces/evidence/marker").write_text("original-work")'
    Docker-Checked compose -p $project exec -T --workdir '/workspace/work/work with spaces' training bash -c 'test -f evidence/marker'
    Docker-Checked compose -p $project stop training
    Docker-Checked compose -p $project up -d training
    Docker-Checked compose -p $project exec -T training python -c 'from pathlib import Path; assert Path("/workspace/work/work with spaces/evidence/marker").read_text()=="original-work"'
    Docker-Checked compose -p $other exec -T training python -c 'from pathlib import Path; assert not Path("/workspace/work/work with spaces").exists()'
    Docker-Checked compose -p $project build training
    Docker-Checked compose -p $project up -d training
    Docker-Checked compose -p $project exec -T training python -c 'from pathlib import Path; assert Path("/workspace/work/work with spaces/evidence/marker").read_text()=="original-work"'
    Docker-Checked compose -p $project exec -T training abb export --output /workspace/export/smoke.zip
    Docker-Checked compose -p $project exec -T training python -c 'import zipfile; z=zipfile.ZipFile("/workspace/export/smoke.zip"); assert z.read("work with spaces/evidence/marker")==b"original-work"'
} finally {
    & docker compose -p $project down --volumes
    & docker compose -p $other down --volumes
}
