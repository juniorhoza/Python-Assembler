#!/usr/bin/env python3
"""
test_hlx_assembler.py
----------------------
HLX Assembler - SRS-Based End-to-End Test Runner
Branch: dev

Tests each .hal input file against the Python assembler directly.
Pass/Fail is determined by SRS expected behavior ONLY.
No reference assembler comparison.

Run from repo root:
    python3 qa/tests/test_hlx_assembler.py

Each test checks:
  - Did the assembler exit with the right code?
  - Did it produce output files when expected?
  - Does the output contain expected error messages?
  - Does the .hlx file contain the exact expected machine code?
"""

import subprocess
import sys
import os

# ── Helpers ───────────────────────────────────────────────────────────────────

PASS_COUNT = 0
FAIL_COUNT = 0
SKIP_COUNT = 0
results = []

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

def run_assembler(hal_file):
    """Run HASM_CLI.py on a .hal file. Returns (exit_code, combined_output)."""
    for ext in [".hlx", ".hll"]:
        old_file = hal_file.replace(".hal", ext)
        if os.path.isfile(old_file):
            os.remove(old_file)
    result = subprocess.run(
        ["python3", "HASM_CLI.py", hal_file],
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)).replace("/qa/tests", "")
    )
    return result.returncode, result.stdout + result.stderr

def hlx_exists(hal_file):
    hlx = hal_file.replace(".hal", ".hlx")
    return os.path.isfile(hlx)

def read_hlx(hal_file):
    """Read .hlx file and return list of non-empty lines."""
    hlx = hal_file.replace(".hal", ".hlx")
    if not os.path.isfile(hlx):
        return []
    with open(hlx) as f:
        return [l.strip() for l in f.readlines() if l.strip()]

def hlx_matches(hal_file, expected_lines):
    """Check .hlx file contains exactly the expected lines."""
    actual = read_hlx(hal_file)
    return actual == expected_lines

def run(tc_id, description, hal_file, checks):
    """Run a single test case."""
    global PASS_COUNT, FAIL_COUNT, SKIP_COUNT

    inputs_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)).replace("/qa/tests", ""),
        "qa/tests/inputs"
    )
    full_path = os.path.join(inputs_dir, hal_file)

    if not os.path.isfile(full_path):
        print(f"  {YELLOW}SKIP{RESET}  {tc_id}  {description}")
        print(f"        Reason: Input file not found: {hal_file}")
        results.append((tc_id, "SKIP", description, "Input file missing"))
        SKIP_COUNT += 1
        return

    exit_code, output = run_assembler(full_path)

    failures = []
    for desc, fn in checks:
        try:
            ok = fn(exit_code, output, full_path)
        except Exception as e:
            ok = False
            failures.append(f"{desc} (exception: {e})")
            continue
        if not ok:
            failures.append(desc)

    if not failures:
        print(f"  {GREEN}PASS{RESET}  {tc_id}  {description}")
        results.append((tc_id, "PASS", description, ""))
        PASS_COUNT += 1
    else:
        print(f"  {RED}FAIL{RESET}  {tc_id}  {description}")
        for f in failures:
            print(f"        ✗ {f}")
        print(f"        Exit code: {exit_code}")
        if hlx_exists(full_path):
            print(f"        .hlx actual:   {read_hlx(full_path)}")
        results.append((tc_id, "FAIL", description, "; ".join(failures)))
        FAIL_COUNT += 1

def skip(tc_id, description, reason):
    """Explicitly skip a test — pending implementation."""
    global SKIP_COUNT
    print(f"  {YELLOW}SKIP{RESET}  {tc_id}  {description}")
    print(f"        Reason: {reason}")
    results.append((tc_id, "SKIP", description, reason))
    SKIP_COUNT += 1

# ── Common check functions ────────────────────────────────────────────────────

def expect_success(exit_code, output, hal_file):
    return exit_code == 0 and hlx_exists(hal_file)

def expect_error(exit_code, output, hal_file):
    return exit_code != 0

def expect_output_contains(keyword):
    def check(exit_code, output, hal_file):
        return keyword.lower() in output.lower()
    return check

def expect_hlx_produced(exit_code, output, hal_file):
    return hlx_exists(hal_file)

def expect_no_hlx(exit_code, output, hal_file):
    return not hlx_exists(hal_file)

def expect_hlx(expected):
    """Check .hlx file matches exactly the expected list of lines."""
    def check(exit_code, output, hal_file):
        return hlx_matches(hal_file, expected)
    return check


# ── Test Cases ────────────────────────────────────────────────────────────────

print("\n" + "="*60)
print(" HLX ASSEMBLER - SRS-BASED END-TO-END TESTS")
print("="*60)

# ── TC-PAR: Parsing & Recognition ────────────────────────────────────────────
print("\n------------------------------------------------------------")
print(" TC-PAR: Parsing & Recognition")
print("------------------------------------------------------------")

run("TC-PAR-001", "Valid HLX syntax — correct machine code produced",
    "TC-PAR-001.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "06",
            "0102","0302","0700","0403","0203","9900",
            "04",
            "0003","0004","9999","9999"
        ])),
    ])

run("TC-PAR-002", "All core directives recognised — correct machine code",
    "TC-PAR-002.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "05",
            "0300","0501","0402","0202","9900",
            "03",
            "0010","0020","9999"
        ])),
    ])

run("TC-PAR-003", ".Block directive — MYARR reserves 5 memory slots",
    "TC-PAR-003.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "03",
            "0305","0205","9900",
            "06",
            "9999","9999","9999","9999","9999","0000"
        ])),
    ])

run("TC-PAR-004", "Invalid directive .ENDING — error with line number",
    "TC-PAR-004.hal", [
        ("Exits with non-zero code", expect_error),
        ("Error mentions unknown directive", expect_output_contains("unknown directive")),
        ("Error includes line number", lambda c,o,f: "line" in o.lower()),
        ("No .hlx produced", expect_no_hlx),
    ])

run("TC-PAR-005", "Forward reference SKIP resolved to address 03",
    "TC-PAR-005.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "05",
            "0300","1103","0401","0200","9900",
            "02",
            "0001","9999"
        ])),
    ])


# ── TC-DIR: Directive & Semantic Rules ───────────────────────────────────────
print("\n------------------------------------------------------------")
print(" TC-DIR: Directive & Semantic Rules")
print("------------------------------------------------------------")

run("TC-DIR-001a", ".alloc first — assembly succeeds with correct output",
    "TC-DIR-001a.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Program structure OK", lambda c,o,f: "program structure ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "04",
            "0300","0401","0201","9900",
            "02",
            "0007","9999"
        ])),
    ])

run("TC-DIR-001b", ".alloc NOT first — error E004, no .hlx produced",
    "TC-DIR-001b.hal", [
        ("Exits with non-zero code", expect_error),
        ("Error E004 reported", expect_output_contains("e004")),
        ("Error references .alloc ordering", lambda c,o,f: "alloc" in o.lower()),
        ("No .hlx produced", expect_no_hlx),
    ])

run("TC-DIR-001c", ".alloc appears twice — warning W004, continues",
    "TC-DIR-001c.hal", [
        ("Assembler handles duplicate .alloc", lambda c,o,f: "alloc" in o.lower()),
        ("Warning W004 issued", lambda c,o,f: "w004" in o.lower() or "duplicate" in o.lower() or "multiple" in o.lower()),
    ])

run("TC-DIR-002", "No .alloc — assembler runs and reports issues",
    "TC-DIR-002.hal", [
        ("Assembler produces output", lambda c,o,f: len(o) > 0),
        ("Lexer and Parser run", lambda c,o,f: "lexer ok" in o.lower() and "parser ok" in o.lower()),
    ])

run("TC-DIR-003a", ".end is last statement — assembly succeeds",
    "TC-DIR-003a.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Program structure OK", lambda c,o,f: "program structure ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "04",
            "0300","0401","0201","9900",
            "02",
            "0005","9999"
        ])),
    ])

run("TC-DIR-003b", ".end missing — error E003, no .hlx produced",
    "TC-DIR-003b.hal", [
        ("Exits with non-zero code", expect_error),
        ("Error E003 reported", lambda c,o,f: "e003" in o.lower() or ".end" in o.lower()),
        ("No .hlx produced", expect_no_hlx),
    ])

run("TC-DIR-003c", "Instruction after .end — error E004, no .hlx produced",
    "TC-DIR-003c.hal", [
        ("Exits with non-zero code", expect_error),
        ("Error mentions after .END", lambda c,o,f: "after" in o.lower() or ("end" in o.lower() and "error" in o.lower())),
        ("No .hlx produced", expect_no_hlx),
    ])

run("TC-DIR-006", ".Block allocates 5 slots — correct addresses",
    "TC-DIR-006.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "03",
            "0305","0205","9900",
            "06",
            "9999","9999","9999","9999","9999","0005"
        ])),
    ])


# ── TC-SYM: Symbol Management ─────────────────────────────────────────────────
print("\n------------------------------------------------------------")
print(" TC-SYM: Symbol Management")
print("------------------------------------------------------------")

run("TC-SYM-001", "Symbol table — 4 labels with correct addresses",
    "TC-SYM-001.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("4 labels found in Pass1", lambda c,o,f: "4 labels" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "11",
            "0300","0501","0402","2302","1109",
            "0300","1600","0400","1005","0202","9900",
            "03",
            "0001","0002","0000"
        ])),
    ])

run("TC-SYM-002", "Duplicate label LOOP — detected, no .hlx produced",
    "TC-SYM-002.hal", [
        ("Duplicate label reported", lambda c,o,f: "duplicate" in o.lower() and "loop" in o.lower()),
        ("No .hlx produced", expect_no_hlx),
    ])

run("TC-SYM-003", "Undefined label MISSING — error E021, no .hlx produced",
    "TC-SYM-003.hal", [
        ("Error E021 reported", lambda c,o,f: "e021" in o.lower() or "undefined" in o.lower()),
        ("MISSING label mentioned", lambda c,o,f: "missing" in o.lower()),
        ("No .hlx produced", expect_no_hlx),
    ])

run("TC-SYM-005", "Opcode table — 14 instructions all encoded correctly",
    "TC-SYM-005.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("14 instructions encoded", lambda c,o,f: "14 instructions encoded" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "14",
            "0100","0300","0501","0601","0701","0801",
            "0402","0202","1600","1700","1300","1113","1013","9900",
            "05",
            "0001","0002","0000","0005"
        ])),
    ])

run("TC-SYM-006", "Location counter — 5 instructions at sequential addresses",
    "TC-SYM-006.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("5 instructions encoded", lambda c,o,f: "5 instructions encoded" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "05",
            "0300","0401","0201","1000","9900",
            "02",
            "0005","0000"
        ])),
    ])


# ── TC-GEN and TC-ERR: Pending Sprint 3 ──────────────────────────────────────
print("\n------------------------------------------------------------")
print(" TC-GEN: Code Generation & Output  [PENDING SPRINT 3]")
print("------------------------------------------------------------")
skip("TC-GEN-001", "Correct machine code generated", "Pending Sprint 3 dev implementation")
skip("TC-GEN-002", "Instructions before data in .hlx", "Pending Sprint 3 dev implementation")
skip("TC-GEN-003", ".hlx output file produced", "Pending Sprint 3 dev implementation")
skip("TC-GEN-004", ".hll listing file produced", "Pending Sprint 3 dev implementation")
skip("TC-GEN-005", "Forward reference resolves correctly", "Pending Sprint 3 dev implementation")

print("\n------------------------------------------------------------")
print(" TC-ERR: Error Handling  [PENDING SPRINT 3]")
print("------------------------------------------------------------")
skip("TC-ERR-001", "Error includes filename and line number", "Pending Sprint 3 dev implementation")
skip("TC-ERR-002", "Error has unique error code", "Pending Sprint 3 dev implementation")
skip("TC-ERR-003", "Multiple non-fatal errors reported in one run", "Pending Sprint 3 dev implementation")
skip("TC-ERR-004", "Fatal error halts assembly, no output", "Pending Sprint 3 dev implementation")
skip("TC-ERR-005", "Exit code 0 on success, non-zero on error", "Pending Sprint 3 dev implementation")


# ── Summary ───────────────────────────────────────────────────────────────────
total = PASS_COUNT + FAIL_COUNT + SKIP_COUNT
print("\n" + "="*60)
print(f" RESULTS:  {PASS_COUNT} PASSED  |  {FAIL_COUNT} FAILED  |  {SKIP_COUNT} SKIPPED  |  {total} TOTAL")
print("="*60)

if FAIL_COUNT > 0:
    print("\n FAILED TESTS:")
    for tc_id, status, desc, reason in results:
        if status == "FAIL":
            print(f"   {tc_id}: {desc}")
            print(f"          {reason}")

if SKIP_COUNT > 0:
    print("\n SKIPPED (pending implementation or missing input):")
    for tc_id, status, desc, reason in results:
        if status == "SKIP":
            print(f"   {tc_id}: {reason}")

print()
sys.exit(0 if FAIL_COUNT == 0 else 1)
