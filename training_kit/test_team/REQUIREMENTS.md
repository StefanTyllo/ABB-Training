# Independent product requirements

These are the oracle. Do not derive expected values from server.py or copy actual output into expected results.

| ID | Required behavior |
|---|---|
| UI-01 | Serial shows Device and hides Host/Port; TCP shows Host/Port and hides Device. Switching works both ways. |
| UI-02 | None hides Password; Password shows Password and requires a nonempty value. Switching works both ways. |
| VAL-01 | TCP port accepts integer endpoints 1 and 65535 and rejects 0, 65536 and non-integer text. Host must be nonempty; Serial Device must be nonempty. |
| SAVE-01 | A valid Save displays Saved. After browser reload, saved connection, active connection values, authentication mode and password are restored. An invalid Save must not overwrite the last valid saved state. |
| ASYNC-01 | Dependent fields and save completion settle asynchronously, 50–300 ms after a change. Tests wait for observable readiness or outcomes, never a fixed sleep. |

Each test begins with factory defaults via a fixture: Serial / COM1 / None; stored TCP values 127.0.0.1 / 502. Hidden values need not be cleared. The application needs no login. Password storage is deliberately synthetic and suitable only for invented test values.
