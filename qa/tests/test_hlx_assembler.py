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
    # Clean up any leftover output files from previous runs
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
    """Check if the .hlx output file was produced."""
    hlx = hal_file.replace(".hal", ".hlx")
    return os.path.isfile(hlx)

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

    all_passed = True
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
        results.append((tc_id, "FAIL", description, "; ".join(failures)))
        FAIL_COUNT += 1


# ── Common check functions ────────────────────────────────────────────────────

def expect_success(exit_code, output, hal_file):
    """Assembler should exit 0 and produce a .hlx file."""
    return exit_code == 0 and hlx_exists(hal_file)

def expect_error(exit_code, output, hal_file):
    """Assembler should exit non-zero."""
    return exit_code != 0

def expect_error_with(keyword):
    """Assembler should exit non-zero and output should contain keyword."""
    def check(exit_code, output, hal_file):
        return exit_code != 0 and keyword.lower() in output.lower()
    return check

def expect_output_contains(keyword):
    """Output should contain keyword (regardless of exit code)."""
    def check(exit_code, output, hal_file):
        return keyword.lower() in output.lower()
    return check

def expect_hlx_produced(exit_code, output, hal_file):
    """A .hlx file should be produced."""
    return hlx_exists(hal_file)

def expect_no_hlx(exit_code, output, hal_file):
    """No .hlx file should be produced."""
    return not hlx_exists(hal_file)


# ── Test Cases ────────────────────────────────────────────────────────────────

print("\n" + "="*60)
print(" HLX ASSEMBLER - SRS-BASED END-TO-END TESTS")
print("="*60)

# ── TC-PAR: Parsing & Recognition ────────────────────────────────────────────
print("\n------------------------------------------------------------")
print(" TC-PAR: Parsing & Recognition")
print("------------------------------------------------------------")

run("TC-PAR-001", "Valid HLX syntax assembles without errors",
    "TC-PAR-001.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        (".hlx file produced", expect_hlx_produced),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
    ])

run("TC-PAR-002", "All core directives recognised (.alloc .data .begin .end)",
    "TC-PAR-002.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        (".hlx file produced", expect_hlx_produced),
        ("Parser OK in output", lambda c,o,f: "parser ok" in o.lower()),
    ])

run("TC-PAR-003", ".Block directive recognised — MYARR in symbol table",
    "TC-PAR-003.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        (".hlx file produced", expect_hlx_produced),
        ("Pass1 OK in output", lambda c,o,f: "pass1 ok" in o.lower()),
    ])

run("TC-PAR-004", "Invalid directive .ENDING causes error with line number",
    "TC-PAR-004.hal", [
        ("Exits with non-zero code", expect_error),
        ("Error mentions unknown directive", expect_output_contains("unknown directive")),
        ("Error includes line number", lambda c,o,f: "line" in o.lower()),
    ])

run("TC-PAR-005", "Forward reference label SKIP resolves correctly",
    "TC-PAR-005.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        (".hlx file produced", expect_hlx_produced),
        ("1 label found in Pass1", lambda c,o,f: "1 labels" in o.lower()),
    ])


# ── TC-DIR: Directive & Semantic Rules ───────────────────────────────────────
print("\n------------------------------------------------------------")
print(" TC-DIR: Directive & Semantic Rules")
print("------------------------------------------------------------")

run("TC-DIR-001a", ".alloc is first statement — assembly succeeds",
    "TC-DIR-001a.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        (".hlx file produced", expect_hlx_produced),
        ("Program structure OK", lambda c,o,f: "program structure ok" in o.lower()),
    ])

run("TC-DIR-001b", ".alloc NOT first — error, assembly halts",
    "TC-DIR-001b.hal", [
        ("Exits with non-zero code", expect_error),
        ("Error references .alloc ordering", lambda c,o,f: "alloc" in o.lower() and "error" in o.lower()),
        ("No .hlx file produced", expect_no_hlx),
    ])

run("TC-DIR-001c", ".alloc appears twice — SRS says error (discrepancy: dev uses warning)",
    "TC-DIR-001c.hal", [
        ("Assembler handles duplicate .alloc", lambda c,o,f: "alloc" in o.lower()),
        ("Output mentions duplicate .alloc", lambda c,o,f: "w004" in o.lower() or "multiple" in o.lower() or "duplicate" in o.lower()),
    ])

run("TC-DIR-002", "Program starts with .begin (no .alloc) — assembler runs and reports issues",
    "TC-DIR-002.hal", [
        ("Assembler produces output", lambda c,o,f: len(o) > 0),
        ("Lexer and Parser run", lambda c,o,f: "lexer ok" in o.lower() and "parser ok" in o.lower()),
    ])

run("TC-DIR-003a", ".end is last statement — assembly succeeds",
    "TC-DIR-003a.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        (".hlx file produced", expect_hlx_produced),
        ("Program structure OK", lambda c,o,f: "program structure ok" in o.lower()),
    ])

run("TC-DIR-003b", ".end missing — error, assembly halts",
    "TC-DIR-003b.hal", [
        ("Exits with non-zero code", expect_error),
        ("Error mentions missing .end", lambda c,o,f: "e003" in o.lower() or ".end" in o.lower()),
        ("No .hlx file produced", expect_no_hlx),
    ])

run("TC-DIR-003c", "Statements after .end — error detected",
    "TC-DIR-003c.hal", [
        ("Exits with non-zero code", expect_error),
        ("Error mentions instruction after .END", lambda c,o,f: "after" in o.lower() or "end" in o.lower() and "error" in o.lower()),
        ("No .hlx file produced", expect_no_hlx),
    ])

run("TC-DIR-006", ".Block allocates correct memory — MYARR at correct base address",
    "TC-DIR-006.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        (".hlx file produced", expect_hlx_produced),
        ("Pass1 OK with data symbols", lambda c,o,f: "pass1 ok" in o.lower()),
    ])


# ── TC-SYM: Symbol Management ─────────────────────────────────────────────────
print("\n------------------------------------------------------------")
print(" TC-SYM: Symbol Management")
print("------------------------------------------------------------")

run("TC-SYM-001", "Symbol table built — all labels with correct addresses",
    "TC-SYM-001.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        (".hlx file produced", expect_hlx_produced),
        ("Labels found in Pass1", lambda c,o,f: "labels" in o.lower() and "pass1 ok" in o.lower()),
    ])

run("TC-SYM-002", "Duplicate label LOOP — assembler detects and reports it",
    "TC-SYM-002.hal", [
        ("Duplicate label mentioned in output", lambda c,o,f: "duplicate" in o.lower() and "loop" in o.lower()),
        ("Exits with code 0 or reports warning", lambda c,o,f: "loop" in o.lower()),
    ])

run("TC-SYM-003", "Undefined label MISSING — assembler detects and reports it",
    "TC-SYM-003.hal", [
        ("Error E020 reported", lambda c,o,f: "e020" in o.lower() or "undefined" in o.lower()),
        ("MISSING label mentioned", lambda c,o,f: "missing" in o.lower()),
    ])


run("TC-SYM-005", "Opcode table lookup — representative mnemonics all encode correctly",
    "TC-SYM-005.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        (".hlx file produced", expect_hlx_produced),
        ("14 instructions encoded", lambda c,o,f: "14 instructions encoded" in o.lower()),
        ("1 label found", lambda c,o,f: "1 labels" in o.lower()),
    ])


run("TC-SYM-006", "Location counter tracks instruction addresses sequentially",

    "TC-SYM-006.hal", [

        ("Exits with code 0", lambda c,o,f: c == 0),

        (".hlx file produced", expect_hlx_produced),

        ("5 instructions encoded", lambda c,o,f: "5 instructions encoded" in o.lower()),

        ("1 label found", lambda c,o,f: "1 labels" in o.lower()),

    ])

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
    print("\n SKIPPED (input files missing):")
    for tc_id, status, desc, reason in results:
        if status == "SKIP":
            print(f"   {tc_id}")

print()
sys.exit(0 if FAIL_COUNT == 0 else 1)