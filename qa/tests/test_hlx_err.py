#!/usr/bin/env python3
"""TC-ERR: Error Handling tests."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_helpers import *

print("\n" + "="*60)
print(" TC-ERR: Error Handling")
print("="*60)

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

if __name__ == "__main__":
    sys.exit(print_summary("TC-ERR"))