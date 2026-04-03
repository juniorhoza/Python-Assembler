#!/usr/bin/env python3
"""TC-CLI: New CLI Features tests."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_helpers import *

print("\n" + "="*60)
print(" TC-CLI: New CLI Features (-o, -s, --cols, .hconfig)")
print("="*60)

# def run_cli(args):
#     """Run HASM_CLI.py with custom arguments."""
#     result = subprocess.run(
#         ["python3", "HASM_CLI.py"] + args,
#         capture_output=True, text=True,
#         cwd=os.path.dirname(os.path.abspath(__file__)).replace("/qa/tests", "")
#     )
#     return result.returncode, result.stdout + result.stderr

# def cli_test(tc_id, description, args, checks):
#     """Run a CLI test with custom arguments."""
#     global PASS_COUNT, FAIL_COUNT
#     code, output = run_cli(args)
#     failures = []
#     for desc, fn in checks:
#         try:
#             ok = fn(code, output)
#         except Exception as e:
#             ok = False
#             failures.append(f"{desc} (exception: {e})")
#             continue
#         if not ok:
#             failures.append(desc)
#     if not failures:
#         print(f"  {GREEN}PASS{RESET}  {tc_id}  {description}")
#         results.append((tc_id, "PASS", description, ""))
#         PASS_COUNT += 1
#     else:
#         print(f"  {RED}FAIL{RESET}  {tc_id}  {description}")
#         for f in failures:
#             print(f"        \u2717 {f}")
#         print(f"        Exit code: {code}")
#         results.append((tc_id, "FAIL", description, "; ".join(failures)))
#         FAIL_COUNT += 1


# TC-CLI-001 through TC-CLI-007 already exist in test_hlx_unit.py
#CLI-001 — --help flag returns exit code 0
#CLI-002 — --help output contains usage info
#CLI-003 — no arguments returns exit code 1
#CLI-004 — wrong extension (.txt) returns exit code 2
#CLI-005 — non-existent file returns exit code 3
#CLI-006 — valid .hal file returns exit code 0
#CLI-007 — file missing .END returns non-zero

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


if __name__ == "__main__":
    sys.exit(print_summary("TC-CLI"))