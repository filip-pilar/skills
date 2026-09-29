# Verify and hand off

Verify a useful domain result from the final loopback origin and a relevant
failure. Use original evidence or synthetic/intercepted responses when replay
would repeat a side effect. Check the controls and customized request/rendering
paths actually used; reuse evidence for unchanged generated guards.

For companions, verify the startup/authentication path and fixed target. For page
extraction, run the completed recipe in the execution browser, including its
ready-state and bounded output. Test changed origin, input, or projection guards.

Complete `FINDINGS.md` with concise evidence: observed action,
mechanism, verification and limits, restart command, and relevant constraints.
Include reuse/pagination/repeatability findings only when they matter. Keep
captured evidence distinct from live replay and substitutions distinct from the
observed mechanism. Remove temporary specs, probes, traces, and captures, then run:

```bash
python3 <skill-directory>/scripts/validate_prototype.py <output-directory>
```

This check catches unfinished scaffolding and leftover captures; it does not prove
correctness or enforce a report format.

Open and reload the final page when supported. Confirm server liveness at handoff,
and provide the exact restart command.
For authenticated flows, check actionable signed-out/wrong-page recovery without
copying secrets between browsers. Report untested paths and partial or blocked
results. The deliverable remains a disposable proof of an undocumented mechanism.
