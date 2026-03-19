# HLX Assembler Bug Log
**Project:** HLX Assembler | **QA Lead:** Ruxandra Flueras
**Branch:** dev | **Commit:** 9b18429 | **Date:** 2026-03-18

---

## BUG-001 — Instructions after .END not detected

| Field | Value |
|---|---|
| **Bug ID** | BUG-001 |
| **TC ID** | TC-DIR-003c |
| **Severity** | High |
| **Status** | Open |
| **Branch** | dev |
| **Commit** | 9b18429 |
| **Date** | 2026-03-18 |
| **Tester** | Ruxandra Flueras |

**Steps to Reproduce:**
Run `python3 HASM_CLI.py qa/tests/inputs/TC-DIR-003c.hal`

**Expected Result:**
Assembler detects `WRITE x` appearing after `.END`, reports an error, and halts. No output files produced.

**Actual Result:**
Assembler reports "Program structure OK" and "Assembler execution OK". `.hlx` and `.hll` written as if file is valid. Exit code 0.

**Root Cause (QA Finding):**
`HASM_Directive_Checker.py` rule R4 only checks for directives after `.END`. Regular instructions after `.END` are silently ignored.

**Fix Notes:** *(dev team fills this in)*

---

## DISC-001 — Duplicate .ALLOC treated as warning, not fatal error

| Field | Value |
|---|---|
| **Bug ID** | DISC-001 |
| **TC ID** | TC-DIR-001c |
| **Severity** | Pending Clarification |
| **Status** | Awaiting Dev Response |
| **Branch** | dev |
| **Commit** | 9b18429 |
| **Date** | 2026-03-18 |
| **Tester** | Ruxandra Flueras |

**Observed Behavior:**
Duplicate `.ALLOC` issues WARNING W004 and continues. Output files written.

**SRS Says:** FR-DIR-001 — `.alloc` must appear exactly once. Error if not.

**Question for Devs:**
> Was treating duplicate `.ALLOC` as a warning (not fatal error) intentional? If so, was it based on the reference assembler behavior? Should this be updated to match the SRS?

**Fix Notes:** *(dev team fills this in)*

---

## DISC-002 — Duplicate label treated as warning, not fatal error

| Field | Value |
|---|---|
| **Bug ID** | DISC-002 |
| **TC ID** | TC-SYM-002 |
| **Severity** | Pending Clarification |
| **Status** | Awaiting Dev Response |
| **Branch** | dev |
| **Commit** | 9b18429 |
| **Date** | 2026-03-18 |
| **Tester** | Ruxandra Flueras |

**Observed Behavior:**
Duplicate label issues a warning and continues using first definition. Output files written.

**SRS Says:** FR-SYM-002 — Detect and report duplicate labels as an error.

**Question for Devs:**
> Was treating duplicate labels as a warning intentional? Should assembly halt on duplicate labels per SRS?

**Fix Notes:** *(dev team fills this in)*

---

## DISC-003 — Undefined label does not halt assembly

| Field | Value |
|---|---|
| **Bug ID** | DISC-003 |
| **TC ID** | TC-SYM-003 |
| **Severity** | Pending Clarification |
| **Status** | Awaiting Dev Response |
| **Branch** | dev |
| **Commit** | 9b18429 |
| **Date** | 2026-03-18 |
| **Tester** | Ruxandra Flueras |

**Observed Behavior:**
ERROR E020 printed for undefined label `MISSING` but assembly continues. Output written with addr 99 substituted.

**SRS Says:** FR-SYM-003 — Detect and report undefined label references as an error.

**Question for Devs:**
> Should assembly halt when an undefined label is encountered, or is continuing with addr 99 an intentional lenient mode? Using addr 99 silently could cause incorrect program execution without the developer knowing.

**Fix Notes:** *(dev team fills this in)*