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
        ("Error includes line number", lambda c,o,f: ":6:" in o or "line 6" in o.lower()),
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

run("TC-DIR-001c", ".alloc appears twice — error E004, assembly halts",
    "TC-DIR-001c.hal", [
        ("Exits with non-zero code", expect_error),
        ("Error E004 reported", expect_output_contains("e004")),
        ("Multiple .ALLOC mentioned", lambda c,o,f: "multiple" in o.lower() or "alloc" in o.lower()),
        ("No .hlx produced", expect_no_hlx),
    ])

run("TC-DIR-002", "No .alloc — error E030 undefined variable, no .hlx",
    "TC-DIR-002.hal", [
        ("Exits with non-zero code", expect_error),
        ("Error E030 reported", expect_output_contains("e030")),
        ("Undefined variable mentioned", lambda c,o,f: "undefined" in o.lower()),
        ("No .hlx produced", expect_no_hlx),
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

run("TC-SYM-002", "Duplicate label LOOP — error E007 with line number, no .hlx produced",
    "TC-SYM-002.hal", [
        ("Error E007 reported", lambda c,o,f: "e007" in o.lower()),
        ("Duplicate label LOOP mentioned", lambda c,o,f: "duplicate" in o.lower() and "loop" in o.lower()),
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


# ── TC-GEN and TC-ERR: Sprint 3 ──────────────────────────────────────
print("\n------------------------------------------------------------")
print(" TC-GEN: Code Generation & Output")
print("------------------------------------------------------------")

run("TC-GEN-001", "Correct machine code generated for each instruction",
    "TC-GEN-001.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "06",
            "0100","0300","0701","0402","0202","9900",
            "03",
            "0003","0004","0000"
        ])),
    ])

run("TC-GEN-002", "Instructions before data in .hlx output",
    "TC-GEN-002.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        (".hlx produced", expect_hlx_produced),
        (".hlx has instructions before data", expect_hlx([
            "03",
            "0300","0401","9900",
            "02",
            "0005","0000"
        ])),
    ])

run("TC-GEN-003", ".hlx output file produced with correct name",
    "TC-GEN-003.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        (".hlx file produced", expect_hlx_produced),
        (".hlx matches expected output", expect_hlx([
            "02",
            "0200","9900",
            "01",
            "0007"
        ])),
    ])

run("TC-GEN-004", ".hll listing file produced",
    "TC-GEN-004.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        (".hll file produced", lambda c,o,f: os.path.isfile(f.replace(".hal",".hll"))),
        ("Output written message for .hll", lambda c,o,f: ".hll" in o.lower()),
    ])

run("TC-GEN-005", "Forward reference DONE resolves to correct address",
    "TC-GEN-005.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "08",
            "0300","2301","1106","1600","0400","1000","0200","9900",
            "02",
            "0001","0010"
        ])),
    ])

print("\n------------------------------------------------------------")
print(" TC-ERR: Error Handling")
print("------------------------------------------------------------")

run("TC-ERR-001", "Error output includes filename and line number",
    "TC-ERR-001.hal", [
        ("Exits with non-zero code", expect_error),
        ("Filename in error output", lambda c,o,f: "tc-err-001.hal" in o.lower()),
        ("Line number in error output", lambda c,o,f: ":7:" in o),
        ("No .hlx produced", expect_no_hlx),
    ])

run("TC-ERR-002", "Error has unique error code",
    "TC-ERR-002.hal", [
        ("Exits with non-zero code", expect_error),
        ("Error code present (E format)", lambda c,o,f: any(f"e{str(i).zfill(3)}" in o.lower() for i in range(1,100))),
        ("No .hlx produced", expect_no_hlx),
    ])

run("TC-ERR-003", "Multiple non-fatal errors all reported in one run",
    "TC-ERR-003.hal", [
        ("Exits with non-zero code", expect_error),
        ("First error reported", lambda c,o,f: "undefined_var1" in o.lower()),
        ("Second error reported", lambda c,o,f: "undefined_var2" in o.lower()),
        ("Both errors in same run", lambda c,o,f: o.lower().count("e030") >= 2),
        ("No .hlx produced", expect_no_hlx),
    ])

run("TC-ERR-003b", "Aggregated error reporting — 3 errors all collected before stopping",
    "TC-ERR-003b.hal", [
        ("Exits with non-zero code", expect_error),
        ("First error reported", lambda c,o,f: "undefined1" in o.lower()),
        ("Second error reported", lambda c,o,f: "undefined2" in o.lower()),
        ("Third error reported", lambda c,o,f: "undefined3" in o.lower()),
        ("All 3 E030 errors in same run", lambda c,o,f: o.lower().count("e030") >= 3),
        ("No .hlx produced", expect_no_hlx),
    ])

run("TC-ERR-004", "Fatal error halts assembly — no output files produced",
    "TC-ERR-004.hal", [
        ("Exits with non-zero code", expect_error),
        ("Fatal error reported", lambda c,o,f: "e003" in o.lower()),
        ("No .hlx produced", expect_no_hlx),
        ("No .hll produced", lambda c,o,f: not os.path.isfile(f.replace(".hal",".hll"))),
    ])

run("TC-ERR-005", "Exit code 0 on success, non-zero on error",
    "TC-ERR-005.hal", [
        ("Exits with code 0 for valid file", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx produced for valid file", expect_hlx_produced),
        (".hlx matches expected output", expect_hlx([
            "02",
            "0200","9900",
            "01",
            "0005"
        ])),
    ])

# ── TC-BLOCK: New .BLOCK syntax (SCRUM-59) ───────────────────────────────────
print("\n------------------------------------------------------------")
print(" TC-BLOCK: .BLOCK New Syntax & Indexed Access (SCRUM-59)")
print("------------------------------------------------------------")

run("TC-BLOCK-001", ".BLOCK initialized =4,=7,=2 — indexed access ARR[0]",
    "TC-BLOCK-001.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "03",
            "0300","0403","9900",
            "04",
            "0004","0007","0002","0000"
        ])),
    ])

run("TC-BLOCK-002", ".BLOCK empty format — 5 uninitialized slots",
    "TC-BLOCK-002.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "01",
            "9900",
            "06",
            "9999","9999","9999","9999","9999","0000"
        ])),
    ])

run("TC-BLOCK-003", ".BLOCK indexed access ARR[0], ARR[1], ARR[2]",
    "TC-BLOCK-003.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "07",
            "0300","0403","0301","0403","0302","0403","9900",
            "04",
            "0010","0020","0030","0000"
        ])),
    ])

run("TC-BLOCK-004", ".BLOCK single value =99 — assembles correctly",
    "TC-BLOCK-004.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "01",
            "9900",
            "03",
            "0099","0000"
        ])),
    ])

run("TC-BLOCK-005", "Single-value .BLOCK indexed access ARR[0] — BUG-002",
    "TC-BLOCK-005.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "02",
            "0300","9900",
            "02",
            "0099"
        ])),
    ])

run("TC-BLOCK-006", ".BLOCK variable index LOAD ARR[i] — dynamic array access",
    "TC-BLOCK-006.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "07",
            "3500","5500","0303","5600","3900","0404","9900",
            "05",
            "0004","0007","0002","0001","0000"
        ])),
    ])

run("TC-BLOCK-007", "STORE ARR[i] — indexed element set via variable index (PENDING-001 resolved)",
    "TC-BLOCK-007.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "07",
            "0304","3500","5500","0303","5600","4000","9900",
            "05",
            "0004","0007","0002","0001","0099"
        ])),
    ])

run("TC-BLOCK-008", ".BLOCK dynamic array loop — LOAD ARR[i] with INCR/STORE pattern",
    "TC-BLOCK-008.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "10",
            "3500","5500","0303","5600","3900","0404","1600","0403","1000","9900",
            "08",
            "0004","0007","0002","0000","0000"
        ])),
    ])

run("TC-BLOCK-009", ".BLOCK uppercase I index — LOAD ARR[I] case insensitive",
    "TC-BLOCK-009.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "07",
            "3500","5500","0303","5600","3900","0404","9900",
            "05",
            "0004","0007","0002","0001","0000"
        ])),
    ])

# ── TC-CON: Constraint & Boundary Conditions ─────────────────────────────────
print("\n------------------------------------------------------------")
print(" TC-CON: Constraint & Boundary Conditions (SCRUM-36)")
print("------------------------------------------------------------")

run("TC-CON-001", "Data memory overflow — ERROR E032 at 101 data slots",
    "TC-CON-001.hal", [
        ("Exits with non-zero code", expect_error),
        ("Error E032 reported", expect_output_contains("e032")),
        ("Memory limit mentioned", lambda c,o,f: "memory limit" in o.lower()),
        ("No .hlx produced", expect_no_hlx),
    ])

run("TC-CON-002", "Instruction memory overflow — ERROR E031 at 101 instructions",
    "TC-CON-002.hal", [
        ("Exits with non-zero code", expect_error),
        ("Error E031 reported", expect_output_contains("e031")),
        ("Memory limit mentioned", lambda c,o,f: "memory limit" in o.lower()),
        ("No .hlx produced", expect_no_hlx),
    ])

run("TC-CON-003", "Immediate value out of range — WARNING W005, truncated",
    "TC-CON-003.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Warning W005 reported", lambda c,o,f: "w005" in o.lower()),
        ("Truncated mentioned", lambda c,o,f: "truncated" in o.lower()),
        (".hlx produced", expect_hlx_produced),
    ])

# ── TC-CLI: New CLI Features ──────────────────────────────────────────────────
print("\n------------------------------------------------------------")
print(" TC-CLI: New CLI Features (-o, -s, --cols, .hconfig)")
print("------------------------------------------------------------")

def run_cli(args):
    """Run HASM_CLI.py with custom arguments."""
    result = subprocess.run(
        ["python3", "HASM_CLI.py"] + args,
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)).replace("/qa/tests", "")
    )
    return result.returncode, result.stdout + result.stderr

def cli_test(tc_id, description, args, checks):
    """Run a CLI test with custom arguments."""
    global PASS_COUNT, FAIL_COUNT
    code, output = run_cli(args)
    failures = []
    for desc, fn in checks:
        try:
            ok = fn(code, output)
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
            print(f"        \u2717 {f}")
        print(f"        Exit code: {code}")
        results.append((tc_id, "FAIL", description, "; ".join(failures)))
        FAIL_COUNT += 1

# TC-CLI-008: Custom output basename -o
for f in ["/tmp/TC-CLI-008-custom.hlx", "/tmp/TC-CLI-008-custom.hll"]:
    if os.path.isfile(f): os.remove(f)

cli_test("TC-CLI-008", "Custom output basename -o — produces named .hlx and .hll",
    ["qa/tests/inputs/TC-CLI-008.hal", "-o", "/tmp/TC-CLI-008-custom"],
    [
        ("Exits with code 0", lambda c,o: c == 0),
        ("Assembler execution OK", lambda c,o: "assembler execution ok" in o.lower()),
        ("Custom .hlx file produced", lambda c,o: os.path.isfile("/tmp/TC-CLI-008-custom.hlx")),
        ("Custom .hll file produced", lambda c,o: os.path.isfile("/tmp/TC-CLI-008-custom.hll")),
        ("Output mentions custom path", lambda c,o: "tc-cli-008-custom" in o.lower()),
    ])

# TC-CLI-009: Symbol table dump -s
sym_file = "qa/tests/inputs/TC-CLI-009.sym"
if os.path.isfile(sym_file): os.remove(sym_file)

cli_test("TC-CLI-009", "Symbol table dump -s — produces .sym with DataTable and LabelTable",
    ["qa/tests/inputs/TC-CLI-009.hal", "-s"],
    [
        ("Exits with code 0", lambda c,o: c == 0),
        ("Assembler execution OK", lambda c,o: "assembler execution ok" in o.lower()),
        (".sym file produced", lambda c,o: os.path.isfile(sym_file)),
        ("DataTable in .sym", lambda c,o: "datatable" in open(sym_file).read().lower() if os.path.isfile(sym_file) else False),
        ("LabelTable in .sym", lambda c,o: "labeltable" in open(sym_file).read().lower() if os.path.isfile(sym_file) else False),
        ("Output mentions .sym", lambda c,o: ".sym" in o.lower()),
    ])

# TC-CLI-010: Valid --cols
cli_test("TC-CLI-010", "Custom column spacing --cols 8,10 — assembles with no errors",
    ["qa/tests/inputs/TC-CLI-010.hal", "--cols", "8,10"],
    [
        ("Exits with code 0", lambda c,o: c == 0),
        ("Assembler execution OK", lambda c,o: "assembler execution ok" in o.lower()),
        ("No warnings", lambda c,o: "warning" not in o.lower()),
    ])

# TC-CLI-011: --cols below minimum
cli_test("TC-CLI-011", "Column spacing below minimum --cols 6,8 — WARNING W006 reported",
    ["qa/tests/inputs/TC-CLI-011.hal", "--cols", "6,8"],
    [
        ("Exits with code 0", lambda c,o: c == 0),
        ("Assembler execution OK", lambda c,o: "assembler execution ok" in o.lower()),
        ("Warning W006 reported", lambda c,o: "w006" in o.lower()),
        ("Warning mentions label column", lambda c,o: "label column" in o.lower()),
    ])

# TC-CLI-012: Invalid --cols format
cli_test("TC-CLI-012", "Invalid --cols format 'abc' — ERROR E009 reported",
    ["qa/tests/inputs/TC-CLI-012.hal", "--cols", "abc"],
    [
        ("Exits with non-zero code", lambda c,o: c != 0),
        ("Error E009 reported", lambda c,o: "e009" in o.lower()),
        ("Invalid format mentioned", lambda c,o: "invalid" in o.lower()),
    ])

# TC-CLI-013: .hconfig file
cli_test("TC-CLI-013", ".hconfig file — assembler reads column config from file",
    ["qa/tests/inputs/TC-CLI-013.hal"],
    [
        ("Exits with code 0", lambda c,o: c == 0),
        ("Assembler execution OK", lambda c,o: "assembler execution ok" in o.lower()),
    ])

# TC-CLI-014: -o combined with -s
for f in ["/tmp/TC-CLI-014-combined.hlx", "/tmp/TC-CLI-014-combined.hll", "/tmp/TC-CLI-014-combined.sym"]:
    if os.path.isfile(f): os.remove(f)

cli_test("TC-CLI-014", "Combined -o and -s — custom basename with symbol dump",
    ["qa/tests/inputs/TC-CLI-014.hal", "-o", "/tmp/TC-CLI-014-combined", "-s"],
    [
        ("Exits with code 0", lambda c,o: c == 0),
        ("Assembler execution OK", lambda c,o: "assembler execution ok" in o.lower()),
        ("Custom .hlx produced", lambda c,o: os.path.isfile("/tmp/TC-CLI-014-combined.hlx")),
        ("Custom .hll produced", lambda c,o: os.path.isfile("/tmp/TC-CLI-014-combined.hll")),
        ("Custom .sym produced", lambda c,o: os.path.isfile("/tmp/TC-CLI-014-combined.sym")),
    ])


# ── EXPLORATORY: New edge cases not covered by formal TCs ─────────────────────
print("\n------------------------------------------------------------")
print(" EXPLORATORY: Edge Cases Found During Testing")
print("------------------------------------------------------------")

run("EXPLORE-001", ".DATA with no value — assembles as 9999 uninitialized",
    "exploratory/explore_data_no_value.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx(["01","9900","01","9999"])),
    ])

run("EXPLORE-002", ".ALLOC 0 — valid, assembles with 0 data slots",
    "exploratory/explore_alloc_zero.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx(["01","9900","00"])),
    ])

run("EXPLORE-003", "BRANCH to itself — valid infinite loop encodes as 1000",
    "exploratory/explore_self_branch.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx(["02","1000","9900","01","0000"])),
    ])

run("EXPLORE-004", "Case insensitive variables — X and x treated as duplicate",
    "exploratory/explore_case_duplicate.hal", [
        ("Exits with non-zero code", expect_error),
        ("ERROR E007 duplicate variable", lambda c,o,f: "e007" in o.lower()),
        ("Variable X mentioned", lambda c,o,f: "'x'" in o.lower()),
        ("No .hlx produced", expect_no_hlx),
    ])

run("EXPLORE-005", "Empty program — no instructions between .BEGIN and .END",
    "exploratory/explore_empty_program.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx(["00","01","0000"])),
    ])

run("EXPLORE-006", "ARR[5] out of bounds literal index — ERROR E030",
    "exploratory/explore_index_oob.hal", [
        ("Exits with non-zero code", expect_error),
        ("ERROR E030 reported", lambda c,o,f: "e030" in o.lower()),
        ("Exceeds block size mentioned", lambda c,o,f: "exceeds" in o.lower()),
        ("No .hlx produced", expect_no_hlx),
    ])

run("EXPLORE-007", "ARR[1] .DATA in data section — overwrites block element at assembly time",
    "exploratory/explore_block_data_set.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected — ARR[1] overwritten from 7 to 99", expect_hlx([
            "01","9900",
            "04",
            "0004","0099","0002","0000"
        ])),
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
    print("\n SKIPPED (pending implementation or missing input):")
    for tc_id, status, desc, reason in results:
        if status == "SKIP":
            print(f"   {tc_id}: {reason}")

print()
sys.exit(0 if FAIL_COUNT == 0 else 1)



