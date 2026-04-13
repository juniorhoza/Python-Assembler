#!/usr/bin/env python3
"""TC-DIR: Directive & Semantic Rules tests."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_helpers import *

print("\n" + "="*60)
print(" TC-DIR: Directive & Semantic Rules")
print("="*60)

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

run("TC-DIR-004", ".DATA = 7 with spaces around = — valid syntax",
    "TC-DIR-004.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "03",
            "0300","0501","9900",
            "02",
            "0007","0003"
        ])),
    ])

run("TC-DIR-005", ".DATA with no = prefix — ERROR E006 invalid format",
    "TC-DIR-005.hal", [
        ("Exits with non-zero code", expect_error),
        ("Error E006 reported", lambda c,o,f: "e006" in o.lower()),
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

if __name__ == "__main__":
    sys.exit(print_summary("TC-DIR"))
