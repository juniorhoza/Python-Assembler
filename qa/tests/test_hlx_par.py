#!/usr/bin/env python3
"""TC-PAR: Parsing & Recognition tests."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_helpers import *

print("\n" + "="*60)
print(" TC-PAR: Parsing & Recognition")
print("="*60)

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

if __name__ == "__main__":
    sys.exit(print_summary("TC-PAR"))
