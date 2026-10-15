# Using GitHub Copilot CLI in GitHub Actions

This guide describes the working setup in **StefanTyllo/ABB-Training**.

## Verified setup

- Workflow: [Copilot authentication test](.github/workflows/copilot-smoke-test.yml)
- Repository secret: `COPILOT`
- CLI authentication variable: `COPILOT_GITHUB_TOKEN`
- Runner: `ubuntu-latest`, with Node.js 22
- Verified CLI version: 1.0.97
- [Successful test run](https://github.com/StefanTyllo/ABB-Training/actions/runs/38589531650), on 14 October 2026

The test returned:

```text
Copilot authentication successful
```

This confirms that the stored token can authenticate Copilot CLI and execute a prompt on an Actions runner. It does not test editing code, running project tests, or opening pull requests.

## Run the existing test

1. Open [the repository's Actions tab](https://github.com/StefanTyllo/ABB-Training/actions).
2. Select **Copilot authentication test**.
3. Select **Run workflow**, choose **main**, and confirm **Run workflow**.
4. Open the new run and inspect the **copilot** job.
5. Check **Test Copilot authentication and execution** for the response. It also appears in the run summary.

The workflow also runs when its own YAML file changes. Other file changes do not trigger it.

## Authentication

The workflow maps your repository secret into the environment:

```yaml
env:
  COPILOT_GITHUB_TOKEN: ${{ secrets.COPILOT }}
```

No interactive `copilot login` is needed in CI.

To replace or renew the token:

1. In your browser, open [GitHub's fine-grained token creation page](https://github.com/settings/personal-access-tokens/new).
2. Choose your **personal account** as the resource owner.
3. Choose a name and expiration.
4. Under **Permissions → Account**, add **Copilot Requests**.
5. Generate the token.
6. In this repository, open **Settings → Secrets and variables → Actions**.
7. Update the secret named **COPILOT** with the new token.

Use a fine-grained token beginning with `github_pat_`. Classic tokens beginning with `ghp_` are unsupported. Store the value as a secret; do not put it in a committed file.

On a phone, open the token creation page in Safari or Chrome.

## How the command works

The existing test uses:

```bash
copilot -p 'Reply with exactly: Copilot authentication successful' \
  --no-ask-user -s --available-tools='' > copilot-response.txt
```

| Option | Purpose |
| --- | --- |
| `-p` | Execute the supplied prompt and exit. |
| `--no-ask-user` | Avoid clarification questions during CI. |
| `-s` | Produce clean response text. |
| `--available-tools=''` | Disable tools for this authentication-only test. |

The workflow writes the response into the Actions summary:

```bash
cat copilot-response.txt >> "$GITHUB_STEP_SUMMARY"
```

## Adapt it to inspect repository code

The current test does not check out the repository. To let Copilot inspect code, add a checkout step and replace the test step with a task-specific command.

For example, a separate manually triggered workflow can summarize the latest commit:

```yaml
name: Copilot commit summary

on:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  summary:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 2
          persist-credentials: false

      - uses: actions/setup-node@v4
        with:
          node-version: '22'

      - name: Install Copilot CLI
        run: npm install -g @github/copilot

      - name: Summarize latest commit
        env:
          COPILOT_GITHUB_TOKEN: ${{ secrets.COPILOT }}
        run: |
          copilot -p 'Use git show HEAD to summarize the latest commit.' \
            -s --no-ask-user \
            --allow-tool='shell(git show:*)' > summary.md
          cat summary.md >> "$GITHUB_STEP_SUMMARY"
```

Save this example as `.github/workflows/copilot-commit-summary.yml` to make it available in Actions. This example is documentation; it has not been added or run.

Remove `--available-tools=''` when adapting the authentication test for tasks that need tools. Grant only the tool permissions that the task needs.

## Adapt it to modify code

For an npm project with lint and test scripts, a possible Copilot step is:

```yaml
- name: Fix lint errors
  env:
    COPILOT_GITHUB_TOKEN: ${{ secrets.COPILOT }}
  run: |
    copilot -p 'Fix ESLint errors. Keep changes limited to lint fixes.' \
      -s --no-ask-user \
      --allow-tool='read, write, shell(npm:*), shell(npx:*)'
```

Check out the code and install its dependencies before this step. Then run ordinary validation commands in separate steps, for example `npm run lint` and `npm test`, so their exit codes determine CI status.

Edits stay on the temporary runner. Add an explicit artifact-upload or pull-request step if you want to retain them. The existing authentication test does not commit, push, or open pull requests.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Secret missing or empty | Confirm that **COPILOT** exists under Actions secrets. |
| Authentication denied | Check expiration and the **Copilot Requests** account permission. |
| Copilot unavailable through your employer | Ask the administrator whether Copilot CLI is enabled. |
| Tool action denied | Add the required `--allow-tool` permission; check that tools are not disabled. |
| Code cannot be found | Add checkout before the Copilot step. |
| Run times out | Inspect logs and narrow the prompt or adjust the five-minute limit. |
| Changes disappear | Export them explicitly from the runner. |

Keep secret-bearing jobs limited to trusted code. Do not use `pull_request_target` to check out and execute untrusted fork changes with this token.

## Official documentation

- [Authentication](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/authenticate-copilot-cli)
- [Running Copilot CLI programmatically](https://docs.github.com/en/copilot/how-tos/copilot-cli/automate-copilot-cli/run-cli-programmatically)
- [Programmatic CLI reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-programmatic-reference)
- [Copilot CLI in GitHub Actions](https://docs.github.com/en/copilot/how-tos/copilot-cli/automate-copilot-cli/automate-with-actions)

## Stage-focused lab rehearsals

The lab runner still invokes GitHub Copilot CLI 1.0.97 with the existing `COPILOT`
secret mapped only to `COPILOT_GITHUB_TOKEN` in its agent step. Independent grading
runs separately without that token. It never invokes a different coding agent.

`training_kit/prompts/` contains common, stage and fresh-transfer instructions.
`training_ci/context_delivery.py` selects the current card section and reading
list without editing the full task card or acceptance contract. Exact prompts,
context snapshots and SHA-256 delivery metadata are saved in each workspace's
evidence directory; context/current-stage.md is host-managed and may change.

Each invocation uses a temporary COPILOT_HOME, --no-custom-instructions and disabled
skill retrieval, so personal instructions/configuration do not enter a rehearsal.
The temporary profile is deleted afterwards; no global settings are changed.
Local scripted rehearsals consequently need the intended token in the environment,
not only a stored interactive login. Classroom guided work keeps normal approvals.
Pinned browser MCP configuration is supplied explicitly for T1/T2; Selenium remains
the test framework. npm uses a writable runner cache. Native Copilot model/effort
can be set through repository variables COPILOT_MODEL/COPILOT_REASONING_EFFORT;
if unset, metadata honestly records CLI defaults rather than a pinned model.

The existing 600-second stage limit is authoritative, with no shorter inner cutoff.
Timeouts retain failure metadata and delivered evidence. Smaller default context
and mandatory-artifact-first prompts do not permit skipping acceptance checks.

Token-free PR checks cover all real card/stage/replay combinations, preservation,
Copilot command isolation, timeout recording and PDF/embedded starter consistency.
Authenticated Copilot rehearsals remain separately dispatchable; passing structural
checks does not establish a new agent acceptance result or a learner pilot.

References: [Copilot programmatic options](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-programmatic-reference),
[configuration directory](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference),
[tool permissions](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/allowing-tools).
