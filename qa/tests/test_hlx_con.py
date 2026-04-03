#!/usr/bin/env python3
"""TC-CON: Constraint & Boundary Conditions tests (SCRUM-36)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_helpers import *

print("\n" + "="*60)
print(" TC-CON: Constraint & Boundary Conditions (SCRUM-36)")
print("="*60)

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

if __name__ == "__main__":
    sys.exit(print_summary("TC-CON"))