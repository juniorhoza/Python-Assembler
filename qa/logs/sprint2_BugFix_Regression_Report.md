# HLX Assembler — Sprint 2 Bug Fix & Regression Report
**Branch:** dev | **Date:** 2026-03-19  
**Tester:** Ruxandra Flueras  
**Commit:** 8edb8cc

---

## Purpose

This report documents the regression testing performed after the Sprint 2
dev build was delivered. The goal was to:

1. Confirm all Sprint 1 frontend tests still pass (no regressions)
2. Verify the Sprint 2 bug fix for TC-DIR-003c
3. Execute the full SRS-based end-to-end test suite against the Sprint 2 build
4. Run byte-for-byte comparison against the reference assembler (HASM_v25.csh)

---

## Sprint 1 Regression — Unit Tests

**Files:** `test_hlx_unit.py` + `test_hlx_edge_cases.py`  
**Purpose:** Verify Sprint 2 dev changes did not break any Sprint 1 frontend functionality.

| Suite | Tests | Result |
|-------|-------|--------|
| Unit Tests (LEX, PAR, STR, CLI) | 43 | ✅ 43/43 PASS |
| Edge Case Tests | 23 | ✅ 23/23 PASS |
| **Total** | **66** | **✅ 66/66 PASS** |

**Conclusion:** No regressions. All Sprint 1 frontend functionality remains intact.

---

## Sprint 2 Bug Fix Verification

### BUG-001 — TC-DIR-003c: Instructions after .END not detected

**Status before fix:** FAIL — assembler silently ignored instructions after `.END`  
**Fix applied by:** Dev team (commit 8edb8cc)  
**Verification:**

Running `python3 HASM_CLI.py qa/tests/inputs/TC-DIR-003c.hal` now produces:

```
ERROR E004: Statement at line 9 appears after .END (line 8).
.END must terminate the program.
```

**Status after fix:** ✅ PASS — assembler correctly detects and reports instructions after `.END`

---

## Full SRS-Based End-to-End Test Results

**File:** `test_hlx_assembler.py`  
**Method:** Each `.hal` input file run through the Python assembler.
Pass/Fail determined by SRS expected behavior only — no reference comparison.

### TC-PAR: Parsing & Recognition (5 tests)

| Test | Description | Result |
|------|-------------|--------|
| TC-PAR-001 | Valid HLX syntax assembles without errors | ✅ PASS |
| TC-PAR-002 | All core directives recognised | ✅ PASS |
| TC-PAR-003 | .Block directive recognised — MYARR in symbol table | ✅ PASS |
| TC-PAR-004 | Invalid directive .ENDING causes error with line number | ✅ PASS |
| TC-PAR-005 | Forward reference label SKIP resolves correctly | ✅ PASS |

### TC-DIR: Directive & Semantic Rules (8 tests)

| Test | Description | Result |
|------|-------------|--------|
| TC-DIR-001a | .alloc is first statement — assembly succeeds | ✅ PASS |
| TC-DIR-001b | .alloc NOT first — error, assembly halts | ✅ PASS |
| TC-DIR-001c | .alloc appears twice — warning issued, continues | ✅ PASS |
| TC-DIR-002 | Program starts with .begin — assembler handles gracefully | ✅ PASS |
| TC-DIR-003a | .end is last statement — assembly succeeds | ✅ PASS |
| TC-DIR-003b | .end missing — error, assembly halts | ✅ PASS |
| TC-DIR-003c | Statements after .end — error detected *(was BUG-001, now fixed)* | ✅ PASS |
| TC-DIR-006 | .Block allocates correct memory | ✅ PASS |

### TC-SYM: Symbol Management (5 tests)

| Test | Description | Result |
|------|-------------|--------|
| TC-SYM-001 | Symbol table built — labels with correct addresses | ✅ PASS |
| TC-SYM-002 | Duplicate label LOOP — assembler detects and reports it | ✅ PASS |
| TC-SYM-003 | Undefined label MISSING — assembler detects and reports it | ✅ PASS |
| TC-SYM-005 | Opcode table lookup — mnemonics encode correctly | ✅ PASS |
| TC-SYM-006 | Location counter tracks addresses sequentially | ✅ PASS |

### TC-GEN: Code Generation & Output (5 tests)

| Test | Description | Result |
|------|-------------|--------|
| TC-GEN-001 | Correct machine code generated | ✅ PASS |
| TC-GEN-002 | Instructions appear before data in .hlx output | ✅ PASS |
| TC-GEN-003 | .hlx output file produced with correct name | ✅ PASS |
| TC-GEN-004 | .hll listing file produced | ✅ PASS |
| TC-GEN-005 | Forward reference DONE resolves to correct address | ✅ PASS |

### TC-ERR: Error Handling (5 tests)

| Test | Description | Result |
|------|-------------|--------|
| TC-ERR-001 | Error output includes filename and line number | ✅ PASS |
| TC-ERR-002 | Error has unique error code | ✅ PASS |
| TC-ERR-003 | Multiple non-fatal errors all reported in one run | ✅ PASS |
| TC-ERR-004 | Fatal error halts assembly — no output files produced | ✅ PASS |
| TC-ERR-005 | Exit code 0 on success, non-zero on error | ✅ PASS |

### SRS Test Summary

| Test Suite | Tests | Pass | Fail |
|------------|-------|------|------|
| Sprint 1 Unit Tests | 66 | 66 | 0 |
| TC-PAR | 5 | 5 | 0 |
| TC-DIR | 8 | 8 | 0 |
| TC-SYM | 5 | 5 | 0 |
| TC-GEN | 5 | 5 | 0 |
| TC-ERR | 5 | 5 | 0 |
| **Total** | **94** | **94** | **0** |

---

## Byte-for-Byte Reference Comparison

**Script:** `run_tests.sh`  
**Reference Assembler:** `HASM_v25.csh` (Professor Jones, version 25 / 2025 Mar 22)  
**Method:** Each `.hal` file assembled by both the Python assembler and the reference
assembler. `.hlx` output files compared after normalizing formatting differences
(trailing spaces stripped, data size zero-padding stripped).

### Results

| Result | Count | Test Cases |
|--------|-------|------------|
| ✅ PASS | 15 | TC-PAR-001, TC-PAR-002, TC-PAR-004, TC-PAR-005, TC-DIR-001a, TC-DIR-001b, TC-DIR-002, TC-DIR-003a, TC-DIR-003b, TC-DIR-003c, TC-SYM-001, TC-SYM-002, TC-SYM-003, TC-SYM-005, TC-SYM-006 |
| ❌ FAIL | 3 | TC-PAR-003, TC-DIR-001c, TC-DIR-006 |
| ⏳ BLOCKED | 13 | TC-CON-001–003, TC-ERR-001–005, TC-GEN-001–005 (input files pending for some) |

### Why the 3 Failures Are Not Bugs

All 3 remaining failures are cases where **our assembler does more than the
reference assembler**, not less. This was confirmed with the dev team.

**TC-PAR-003 and TC-DIR-006 — .BLOCK directive:**
The Python assembler supports `.BLOCK` as an array allocation directive
(FR-PAR-003, FR-DIR-006). The reference assembler does not support `.BLOCK`
at all — it skips those slots entirely in the output. Our assembler correctly
writes the allocated memory slots to the `.hlx` file. This is an intentional
improvement over the reference.

**TC-DIR-001c — Duplicate .ALLOC:**
The reference assembler treats duplicate `.ALLOC` as a fatal error. Our
assembler issues warning W004 and continues using the first definition —
a more lenient and user-friendly behavior. The machine code produced is
correct. This is an intentional design decision confirmed by the dev team.

### Formatting Note

Before comparison, both outputs were normalized by:
- Stripping trailing spaces from instruction lines
- Stripping zero-padding from the data size line (e.g. `04` → `4`)

These were purely cosmetic differences in `output.py` that did not affect
machine code correctness. After normalization, the 15 passing tests produce
byte-for-byte identical output to the reference assembler.

---

## Overall Conclusion

The Sprint 2 build is in good health:

- ✅ **94/94 SRS-based tests passing** — all features working correctly
- ✅ **66/66 Sprint 1 regression tests passing** — no regressions
- ✅ **BUG-001 confirmed fixed** — instructions after `.END` now correctly detected
- ✅ **15/18 reference comparisons passing** — machine code correct on all comparable tests
- ℹ️ **3 reference mismatches** — intentional improvements over reference (`.BLOCK` support, lenient duplicate `.ALLOC`) — confirmed with dev team, not bugs
- ⏳ **13 tests blocked** — awaiting TC-CON input files (Sprint 3 scope)
