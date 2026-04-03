#!/usr/bin/env python3
"""
test_helpers.py
---------------
Shared helpers for all HLX Assembler test suites.
Import this in each category test file.
"""

import subprocess
import sys
import os

PASS_COUNT = 0
FAIL_COUNT = 0
SKIP_COUNT = 0
results = []

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

def repo_root():
    return os.path.dirname(os.path.abspath(__file__)).replace("/qa/tests", "")

def inputs_dir():
    return os.path.join(repo_root(), "qa/tests/inputs")

def run_assembler(hal_file):
    for ext in [".hlx", ".hll"]:
        old_file = hal_file.replace(".hal", ext)
        if os.path.isfile(old_file):
            os.remove(old_file)
    result = subprocess.run(
        ["python3", "HASM_CLI.py", hal_file],
        capture_output=True, text=True,
        cwd=repo_root()
    )
    return result.returncode, result.stdout + result.stderr

def run_cli(args):
    result = subprocess.run(
        ["python3", "HASM_CLI.py"] + args,
        capture_output=True, text=True,
        cwd=repo_root()
    )
    return result.returncode, result.stdout + result.stderr

def hlx_exists(hal_file):
    return os.path.isfile(hal_file.replace(".hal", ".hlx"))

def read_hlx(hal_file):
    hlx = hal_file.replace(".hal", ".hlx")
    if not os.path.isfile(hlx):
        return []
    with open(hlx) as f:
        return [l.strip() for l in f.readlines() if l.strip()]

def hlx_matches(hal_file, expected_lines):
    return read_hlx(hal_file) == expected_lines

def run(tc_id, description, hal_file, checks):
    global PASS_COUNT, FAIL_COUNT, SKIP_COUNT
    full_path = os.path.join(inputs_dir(), hal_file)
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
            print(f"        \u2717 {f}")
        print(f"        Exit code: {exit_code}")
        if hlx_exists(full_path):
            print(f"        .hlx actual:   {read_hlx(full_path)}")
        results.append((tc_id, "FAIL", description, "; ".join(failures)))
        FAIL_COUNT += 1

def cli_test(tc_id, description, args, checks):
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

def skip(tc_id, description, reason):
    global SKIP_COUNT
    print(f"  {YELLOW}SKIP{RESET}  {tc_id}  {description}")
    print(f"        Reason: {reason}")
    results.append((tc_id, "SKIP", description, reason))
    SKIP_COUNT += 1

def print_summary(suite_name=""):
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
        print("\n SKIPPED:")
        for tc_id, status, desc, reason in results:
            if status == "SKIP":
                print(f"   {tc_id}: {reason}")
    print()
    return FAIL_COUNT

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
    def check(exit_code, output, hal_file):
        return hlx_matches(hal_file, expected)
    return check