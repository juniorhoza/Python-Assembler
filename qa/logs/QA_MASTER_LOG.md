# HLX Assembler — QA Master Log
**Project:** HLX Assembler | **Team:** Assembler Warriors  
**QA Lead:** Ruxandra Flueras | **QA Tester:** Elizabeth Uzoho  
**Dev Team:** Frank Junior Hoza Longfor, Javonte Carter  
**Last Updated:** 2026-03-23

---

## Overview

This document is the single source of truth for all QA activity across all sprints.
It covers what was tested, what was found, what was fixed, and the current state
of every test suite. Anyone reading this file can trace the full history of QA
from Sprint 1 through Sprint 3.

---

## Current Test Suite Status (Sprint 3 — as of 2026-03-23)

| Suite | Script | Result |
|-------|--------|--------|
| Unit Tests | `test_hlx_unit.py` | **43 PASS / 0 FAIL** ✅ |
| Edge Cases | `test_hlx_edge_cases.py` | **23 PASS / 0 FAIL** ✅ |
| SRS End-to-End | `test_hlx_assembler_improved.py` | **18 PASS / 0 FAIL / 10 SKIP** ✅ |
| Reference Comparison | `run_tests.sh` | **25 PASS / 3 FAIL (intentional) / 3 BLOCKED** ✅ |

**Grand total: 84 test cases. 0 unexpected failures.**

The 3 reference comparison failures are intentional — our assembler supports
`.BLOCK` (which the reference does not), and handles duplicate `.ALLOC` differently.
The 10 skipped SRS tests are pending Sprint 3 TC-CON input files.

---

## How to Run All Tests

Always run from the `dev` branch:

```bash
git checkout dev
rm -f qa/tests/inputs/*.hlx qa/tests/inputs/*.hll

# Sprint 1 regression
python3 qa/tests/test_hlx_unit.py
python3 qa/tests/test_hlx_edge_cases.py

# SRS end-to-end (primary test suite)
python3 qa/tests/test_hlx_assembler_improved.py

# Reference comparison
bash qa/scripts/run_tests.sh
```

---

## Sprint 1 — Frontend Testing (2026-03-18)

### What Was Tested
Sprint 1 focused on the assembler frontend: lexer, parser, program structure
checker, and CLI argument handling.

### Test Scripts Written
- `test_hlx_unit.py` — 43 unit tests covering lexer tokens, parser statements,
  program structure rules, and CLI exit codes
- `test_hlx_edge_cases.py` — 23 edge case tests based on real student file
  patterns seen in previous semesters

### Results
```
test_hlx_unit.py:       43 PASSED | 0 FAILED
test_hlx_edge_cases.py: 23 PASSED | 0 FAILED
```

### Key Findings
- Lexer correctly tokenizes all directive and instruction types
- Parser correctly handles .BLOCK directive (extension beyond reference assembler)
- Program structure checker enforces all ordering rules
- CLI returns correct exit codes for all argument scenarios
- All 12 real student file patterns parsed correctly

### Notes
No bugs found in Sprint 1. All 66 frontend tests passing.

---

## Sprint 2 — SRS-Based End-to-End Testing (2026-03-18 to 2026-03-19)

### What Was Tested
Sprint 2 focused on end-to-end assembly — running complete `.hal` programs
through the full assembler pipeline and verifying the `.hlx` machine code output
against the SRS requirements and the reference assembler.

### Test Scripts Written
- `test_hlx_assembler.py` — initial SRS-based end-to-end test runner
- `run_tests.sh` — reference comparison script (diffs our `.hlx` vs reference)

### Test Input Files Created
TC-PAR-001 through TC-PAR-005, TC-DIR-001a/b/c, TC-DIR-002, TC-DIR-003a/b/c,
TC-DIR-006, TC-SYM-001/002/003/005/006

### Initial Results (commit 9b18429)
```
run_tests.sh: 3 PASS | 15 FAIL | 13 BLOCKED
```

### Root Cause Analysis
All 15 failures had the same root cause — trailing spaces and data size
formatting differences between our assembler and the reference. Machine code
values were 100% correct. After normalization (strip trailing spaces, normalize
data size), all outputs were identical to the reference.

Two tests (TC-PAR-003, TC-DIR-006) had an additional difference: our assembler
writes `.BLOCK` slots as `9999` in the `.hlx` file, the reference omits them.
This was confirmed as intentional — our implementation is correct per the SRS.

### Discrepancies Found and Raised with Dev Team
| ID | Issue | Status at End of Sprint 2 |
|----|-------|--------------------------|
| DISC-001 | Duplicate `.ALLOC` issued warning, SRS says fatal error | Raised |
| DISC-002 | Duplicate label issued warning, SRS says fatal error | Raised |
| DISC-003 | Undefined label continued with addr 99, SRS says halt | Raised |

### BUG-001 Found
**TC-DIR-003c:** Instructions after `.END` were silently ignored. Assembler
reported "Program structure OK" and wrote output files when it should have
halted with an error. Root cause: `HASM_Directive_Checker.py` rule R4 only
checked for directives after `.END`, not instructions.

**Reported to dev team on 2026-03-18. Fixed in commit 8edb8cc.**

### Post-Fix Results (commit 8edb8cc)
```
run_tests.sh (normalized): 15 PASS | 3 FAIL (intentional) | 13 BLOCKED
test_hlx_unit.py:          43 PASS | 0 FAIL  (regression confirmed)
test_hlx_edge_cases.py:    23 PASS | 0 FAIL  (regression confirmed)
```

---

## Sprint 3 — Improved Testing & Discrepancy Resolution (2026-03-23)

### What Changed
The dev team resolved all Sprint 2 discrepancies:
- DISC-001: Duplicate `.ALLOC` updated to fatal error E004
- DISC-002: Duplicate label updated to fatal error (halts assembly)
- DISC-003: Undefined label updated to halt with ERROR E021
- DISC-004 (new): Duplicate label message was missing ERROR prefix and error
  code. Dev team assigned ERROR E007. Resolved same day.

### Test Script Improvements
The original `test_hlx_assembler.py` used lenient keyword checks that would
pass even if the assembler produced wrong machine code. It was replaced with
`test_hlx_assembler_improved.py` which checks exact `.hlx` output line by line.

**Verification method:** For every valid program test, the expected machine
code was manually calculated using the opcode table, then verified against
the actual assembler output, then hardcoded into the test. Example:

```
LOAD c where c=addr02 → opcode 03 + addr 02 = 0302 ✓
BRT SKIP where SKIP=iaddr03 → opcode 11 + addr 03 = 1103 ✓
```

**Sabotage test:** The script was verified by deliberately breaking
`services/pass2.py` (changing no-operand encoding from `opcode+00` to
`opcode+99`). This caused 10 immediate failures — confirming the script
genuinely checks correctness, not just that the assembler ran.

### New Test Input Files Created
TC-GEN-001 through TC-GEN-005, TC-ERR-001 through TC-ERR-005

### STR-007 Fix
Unit test STR-007 was updated — it previously expected duplicate `.ALLOC`
to produce a warning (W004) but the dev team changed it to a fatal error
(E004). Test updated to match new behavior.

### Final Results (commit 94095de)
```
test_hlx_unit.py:                43 PASS | 0 FAIL
test_hlx_edge_cases.py:          23 PASS | 0 FAIL
test_hlx_assembler_improved.py:  18 PASS | 0 FAIL | 10 SKIP
run_tests.sh:                    25 PASS | 3 FAIL (intentional) | 3 BLOCKED
```

---

## Bug & Discrepancy Tracker

| ID | TC | Title | Found | Fixed | Status |
|----|-----|-------|-------|-------|--------|
| BUG-001 | TC-DIR-003c | Instructions after .END not detected | 2026-03-18 | 2026-03-19 (8edb8cc) | ✅ Fixed |
| DISC-001 | TC-DIR-001c | Duplicate .ALLOC was warning not fatal error | 2026-03-18 | 2026-03-19 | ✅ Resolved |
| DISC-002 | TC-SYM-002 | Duplicate label was warning not fatal error | 2026-03-18 | 2026-03-19 | ✅ Resolved |
| DISC-003 | TC-SYM-003 | Undefined label continued instead of halting | 2026-03-18 | 2026-03-19 | ✅ Resolved |
| DISC-004 | TC-SYM-002 | Duplicate label message missing ERROR prefix and code | 2026-03-23 | 2026-03-23 | ✅ Resolved (E007) |

**0 open bugs. 0 open discrepancies.**

---

## Test Run History

```
------------------------------------------------------------
Sprint 1 | 2026-03-18 | Commit: 9b18429
  test_hlx_unit.py:       43 PASS | 0 FAIL
  test_hlx_edge_cases.py: 23 PASS | 0 FAIL
  Frontend testing complete. No bugs found.
------------------------------------------------------------
Sprint 2 Initial | 2026-03-18 | Commit: 9b18429
  run_tests.sh: 3 PASS | 15 FAIL | 13 BLOCKED
  Root cause: formatting differences + BUG-001 found (TC-DIR-003c)
  All 15 FAIL caused by trailing spaces / data size formatting (cosmetic)
------------------------------------------------------------
Sprint 2 Post-Fix | 2026-03-19 | Commit: 8edb8cc
  run_tests.sh (normalized): 15 PASS | 3 FAIL (intentional) | 13 BLOCKED
  BUG-001 fixed. Regression confirmed: 66/66 unit tests still passing.
  3 intentional FAIL: TC-PAR-003, TC-DIR-001c, TC-DIR-006
------------------------------------------------------------
Sprint 3 Final | 2026-03-23 | Commit: 94095de
  test_hlx_unit.py:                43 PASS | 0 FAIL
  test_hlx_edge_cases.py:          23 PASS | 0 FAIL
  test_hlx_assembler_improved.py:  18 PASS | 0 FAIL | 10 SKIP
  run_tests.sh:                    25 PASS | 3 FAIL (intentional) | 3 BLOCKED
  All discrepancies resolved. Improved test script sabotage-verified.
  DISC-004 (E007) resolved. STR-007 updated.
------------------------------------------------------------
```

---

## Known Intentional Differences from Reference Assembler

These 3 tests will always show as FAIL in the reference comparison.
They are NOT bugs — they are intentional design choices.

| TC | Reason |
|----|--------|
| TC-PAR-003 | Our assembler writes .BLOCK slots as 9999 in .hlx. Reference omits them. Our behavior is correct per SRS. |
| TC-DIR-001c | Our assembler now halts on duplicate .ALLOC (E004). Reference assembler behavior differs. Both halt — just different exit codes. |
| TC-DIR-006 | Same as TC-PAR-003 — .BLOCK slot output difference. |

---

## Pending Items (Sprint 3+)

| Item | Owner | Notes |
|------|-------|-------|
| TC-CON-001/002/003 input files | QA | Memory overflow, case enforcement, operand range |
| Activate TC-GEN/TC-ERR in improved script | QA | Input files exist, awaiting dev completion |
| Configurable listing file test | QA | Professor requested feature — test design TBD |

---

## File Index

| File | Purpose |
|------|---------|
| `qa/tests/test_hlx_assembler_improved.py` | **Primary test suite** — exact output verification, sabotage-tested |
| `qa/tests/test_hlx_unit.py` | Sprint 1 unit tests — lexer, parser, structure, CLI |
| `qa/tests/test_hlx_edge_cases.py` | Sprint 1 edge cases — real student file patterns |
| `qa/tests/test_hlx_assembler.py` | Original lenient test runner — kept for reference |
| `qa/scripts/run_tests.sh` | Reference comparison script |
| `qa/logs/BUG_LOG.md` | Detailed bug and discrepancy records |
| `qa/logs/SUMMARY.log` | Test run history — all sprints |
| `qa/tests/inputs/` | All .hal test input files |
