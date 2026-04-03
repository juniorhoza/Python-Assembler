#!/usr/bin/env python3
"""
run_all_tests.py — Master test runner for HLX Assembler.
Run from repo root: python3 qa/tests/run_all_tests.py
"""
import subprocess
import sys
import os

GREEN  = "\033[92m"
RED    = "\033[91m"
RESET  = "\033[0m"

SUITES = [
    ("test_hlx_unit.py",        "Unit Tests"),
    ("test_hlx_edge_cases.py",  "Edge Case Tests"),
    ("test_hlx_par.py",         "TC-PAR: Parsing & Recognition"),
    ("test_hlx_dir.py",         "TC-DIR: Directive & Semantic Rules"),
    ("test_hlx_sym.py",         "TC-SYM: Symbol Management"),
    ("test_hlx_gen.py",         "TC-GEN: Code Generation & Output"),
    ("test_hlx_err.py",         "TC-ERR: Error Handling"),
    ("test_hlx_block.py",       "TC-BLOCK: New .BLOCK Array Feature"),
    ("test_hlx_con.py",         "TC-CON: Constraint & Boundary Conditions"),
    ("test_hlx_cli.py",         "TC-CLI: New CLI Features"),
    ("test_hlx_exploratory.py", "EXPLORATORY: Edge Cases"),
]

def run_suite(script):
    result = subprocess.run(
        ["python3", os.path.join("qa/tests", script)],
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)).replace("/qa/tests", "")
    )
    for line in result.stdout.splitlines():
        if "RESULTS:" in line:
            try:
                passed = int(line.split("PASSED")[0].split()[-1])
                failed = int(line.split("FAILED")[0].split()[-1].strip("|").strip())
                if "SKIPPED" in line:
                    skipped = int(line.split("SKIPPED")[0].split()[-1].strip("|").strip())
                else:
                    skipped = 0
                return passed, failed, skipped, result.stdout
            except:
                pass
    return 0, 0, 0, result.stdout

print("\n" + "="*70)
print(" HLX ASSEMBLER — FULL TEST SUITE")
print("="*70)

total_pass = total_fail = total_skip = 0

for script, label in SUITES:
    passed, failed, skipped, output = run_suite(script)
    total_pass += passed
    total_fail += failed
    total_skip += skipped
    status = f"{GREEN}PASS{RESET}" if failed == 0 else f"{RED}FAIL{RESET}"
    print(f"  {status}  {label}")
    print(f"        {passed} passed | {failed} failed | {skipped} skipped")
    if failed > 0:
        for line in output.splitlines():
            if "FAIL  " in line and "RESULTS" not in line:
                print(f"        {line.strip()}")

print("\n" + "="*70)
total = total_pass + total_fail + total_skip
print(f" TOTAL:  {total_pass} PASSED  |  {total_fail} FAILED  |  {total_skip} SKIPPED  |  {total} TOTAL")
print("="*70)
print()
sys.exit(0 if total_fail == 0 else 1)