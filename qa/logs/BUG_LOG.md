# HLX Assembler Bug Log
**Project:** HLX Assembler | **QA Lead:** Ruxandra Flueras
**Last Updated:** 2026-03-23

---

## BUG-001 — Instructions after .END not detected

| Field | Value |
|---|---|
| **Bug ID** | BUG-001 |
| **TC ID** | TC-DIR-003c |
| **Severity** | High |
| **Status** | ✅ Fixed |
| **Branch** | dev |
| **Commit Found** | 9b18429 |
| **Commit Fixed** | 8edb8cc |
| **Date Found** | 2026-03-18 |
| **Date Fixed** | 2026-03-19 |
| **Tester** | Ruxandra Flueras |

**Steps to Reproduce:**
Run `python3 HASM_CLI.py qa/tests/inputs/TC-DIR-003c.hal`

**Expected Result:**
Assembler detects `WRITE x` appearing after `.END`, reports an error, and halts. No output files produced.

**Actual Result (before fix):**
Assembler reported "Program structure OK" and "Assembler execution OK". `.hlx` and `.hll` written as if file is valid. Exit code 0.

**Root Cause (QA Finding):**
`HASM_Directive_Checker.py` rule R4 only checked for directives after `.END`. Regular instructions after `.END` were silently ignored.

**Fix Applied:**
Dev team updated R4 in `HASM_Directive_Checker.py` to also flag regular instructions appearing after `.END`.

**Verified:**
After fix, running TC-DIR-003c now produces:
`ERROR E004: Statement at line 9 appears after .END (line 8). .END must terminate the program.`
Exit code non-zero, no `.hlx` produced. TC-DIR-003c now PASS. ✅

---

## DISC-001 — Duplicate .ALLOC behavior

| Field | Value |
|---|---|
| **Bug ID** | DISC-001 |
| **TC ID** | TC-DIR-001c |
| **Severity** | N/A |
| **Status** | ✅ Resolved — Intentional Design, Updated to Fatal Error |
| **Branch** | dev |
| **Commit** | 8edb8cc |
| **Date** | 2026-03-18 |
| **Tester** | Ruxandra Flueras |

**Original Observation:**
Duplicate `.ALLOC` issued WARNING W004 and continued. Output files written.

**Resolution:**
Dev team updated the assembler to treat duplicate `.ALLOC` as a fatal error (ERROR E004), matching the SRS. Assembly now halts and no `.hlx` is produced.

**Verified:**
Running TC-DIR-001c now produces:
`ERROR E004: Multiple .ALLOC directives at lines [1, 4]. Only one .ALLOC directive is allowed.`
Exit code 5 (non-zero), no `.hlx` produced. ✅

---

## DISC-002 — Duplicate label behavior

| Field | Value |
|---|---|
| **Bug ID** | DISC-002 |
| **TC ID** | TC-SYM-002 |
| **Severity** | N/A |
| **Status** | ✅ Resolved — Updated to Fatal Error |
| **Branch** | dev |
| **Commit** | 8edb8cc |
| **Date** | 2026-03-18 |
| **Tester** | Ruxandra Flueras |

**Original Observation:**
Duplicate label issued a warning and continued using first definition. Output files written.

**Resolution:**
Dev team updated the assembler to treat duplicate labels as a fatal error. Assembly now halts after structure checking. No `.hlx` produced.

**Verified:**
Running TC-SYM-002 now produces:
`Line 9: duplicate label 'LOOP' previously defined at line 6.`
Assembly halts, no `.hlx` produced. ✅

**Minor Open Item — see DISC-004 below.**

---

## DISC-003 — Undefined label behavior

| Field | Value |
|---|---|
| **Bug ID** | DISC-003 |
| **TC ID** | TC-SYM-003 |
| **Severity** | N/A |
| **Status** | ✅ Resolved — Confirmed Intentional Design |
| **Branch** | dev |
| **Commit** | 8edb8cc |
| **Date** | 2026-03-18 |
| **Tester** | Ruxandra Flueras |

**Original Observation:**
ERROR E020 printed for undefined label `MISSING` but assembly continued with addr 99 substituted.

**Resolution:**
After team discussion, this was confirmed as intentional lenient mode behavior. The assembler now correctly reports ERROR E021 with the line number and halts after Pass1. No `.hlx` produced.

**Verified:**
Running TC-SYM-003 now produces:
`ERROR E021 Line 7: undefined label 'MISSING'`
Assembly halts after Pass1, no `.hlx` produced. ✅

---

## DISC-004 — Duplicate label message missing ERROR prefix and error code

| Field | Value |
|---|---|
| **Bug ID** | DISC-004 |
| **TC ID** | TC-SYM-002 |
| **Severity** | Low |
| **Status** | Open — Awaiting Dev Response |
| **Branch** | dev |
| **Commit** | 8edb8cc |
| **Date** | 2026-03-23 |
| **Tester** | Ruxandra Flueras |

**Observed Behavior:**
When a duplicate label is detected, the message is:
`Line 9: duplicate label 'LOOP' previously defined at line 6.`
No `ERROR` prefix and no error code.

**Compare with TC-SYM-003 which correctly shows:**
`ERROR E021 Line 7: undefined label 'MISSING'`

**SRS Says:** FR-ERR-002 — Error messages should have unique error codes.

**Question for Devs:**
> The duplicate label message has no ERROR prefix and no error code, unlike other error messages. Should it follow the same format as E021? What error code should be assigned to duplicate label detection?

**Fix Notes:** *(dev team fills this in)*
---

## DISC-004 — Duplicate label message missing ERROR prefix and error code

| Field | Value |
|---|---|
| **Bug ID** | DISC-004 |
| **TC ID** | TC-SYM-002 |
| **Severity** | Low |
| **Status** | ✅ Resolved — Fixed in Sprint 3 |
| **Branch** | dev |
| **Commit Found** | 8edb8cc |
| **Commit Fixed** | latest dev |
| **Date Found** | 2026-03-23 |
| **Date Fixed** | 2026-03-23 |
| **Tester** | Ruxandra Flueras |

**Original Observation:**
Message had no ERROR prefix and no error code:
`Line 9: duplicate label 'LOOP' previously defined at line 6.`

**Fix Applied:**
Dev team assigned error code E007. Now correctly reports:
`ERROR E007: duplicate label 'LOOP' previously defined at line 6.`

**Verified:**
TC-SYM-002 test updated to check for E007. 18/18 tests passing. ✅
