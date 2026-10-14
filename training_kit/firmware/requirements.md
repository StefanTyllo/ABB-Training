# Exercise contracts

## FW1

- Each invocation handles one primitive and prints one JSON value to stdout on
  success. Invalid commands/parameters/values report stderr and exit nonzero.
- `--workdir PATH` precedes the subcommand; default is `.device` relative to cwd.
  Commands persist mutable state in `PATH/state.json`. Reads/probes do not mutate.
- `init --case demo|transfer` creates state once. Both cases start at baud 9600.
  Demo is SIM-017 / expected 19200; transfer is SIM-083 / expected 38400.
  Both use firmware 1.4.2. `fw1/expected.json` is the fixed configuration reference:
  exercise code must not change it. This separation is logical, not security.
- `read --field identity|firmware|config|faults`, `logs`, and `probe` expose
  independent observations. A mismatch produces LINK_TIMEOUT and a failed probe;
  matching baud produces no active fault and a successful probe. Historical boot
  timeout remains in logs after recovery; logs are not the current fault register.
- `set --parameter baud --value INT` accepts 1200..115200 inclusive; all other
  parameter names and out-of-range values fail without modifying state. Accepted
  writes append a log entry. Capturing before/after evidence is learner work.
- Simulator scope: one operator, local files, deterministic link comparison.
  No hardware timing, authentication, concurrency, retries, or crash recovery.

## FW2

- A packet is exactly six bytes: `A5 02 sequence low high checksum`.
  Sequence is unsigned 8-bit; low/high encode a signed two's-complement 16-bit
  little-endian value. Checksum is XOR of the preceding five bytes.
- `Parser` is initialized to zero once per stream. Every feed call continues
  that stream. Calls may contain zero bytes, partial packets, many packets, or
  noise. Partial state survives chunk boundaries. There is no timeout behavior.
- Resynchronization: discard leading bytes until A5. Once a second byte exists,
  reject any length other than 02 by discarding only the leading A5 and rescanning.
  Wait for six bytes for a candidate with valid header. On checksum failure,
  discard only its first byte and rescan all remaining bytes, preserving a possible
  partial candidate. On success, emit once and consume all six bytes. A5 inside a
  valid payload/sequence/checksum is ordinary data. At end-of-stream, incomplete
  data emits nothing. A fresh process starts a fresh stream.
- CLI arguments are chunks of contiguous, even-length hexadecimal (either case).
  Empty chunks are accepted; maximum is 4096 bytes per argument. Reject malformed
  or longer chunks with nonzero exit and stderr before any stdout. No arguments
  emit `[]`. Successful output is a JSON array of `{sequence, value}` objects.
- Demo `A5 02 07 85 FF DA` means sequence 7, value -123. Transfer
  `A5 02 2A 00 F8 75` means sequence 42, value -2048.
